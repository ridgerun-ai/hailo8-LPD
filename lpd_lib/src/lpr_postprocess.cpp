/**
 * Copyright (c) 2021-2022 Hailo Technologies Ltd. All rights reserved.
 * Distributed under the LGPL license (https://www.gnu.org/licenses/old-licenses/lgpl-2.1.txt)
 * Copyright (c) 2025 RidgeRun <support@ridgerun.ai>. All rights reserved.
 **/

#include <gst/video/video-format.h>
#include <iostream>
#include <map>
#include <typeinfo>
#include <math.h>

// Hailo includes
#include "hailo_objects.hpp"
#include "hailo_common.hpp"
#include "lpr_postprocess.hpp"
#include "image.hpp"

// Open source includes
#include <opencv2/opencv.hpp>
#include <opencv2/imgcodecs.hpp>
#include <opencv2/imgproc.hpp>
#include <opencv2/core.hpp>

#define DEBUG (0)

#define PLATE_SCALE_FACTOR (1.5f)
#define LP_OVERLAP_THRESHOLD (0.80f)
#define LP_ZOOM_OVERLAY_THICKNESS (3)
#define PLATES_OVERLAP_THRESHOLD (0.01f)
#define MIN_LP_AREA (0.0005f)
#define MIN_LP_OUTPUT_WIDTH  64
#define MIN_LP_OUTPUT_HEIGHT 32

struct PlateCandidate {
    HailoDetectionPtr detection;
    HailoBBox bbox;
    float confidence;
};

/**
 * @brief Computes the Intersection over Union (IoU) between two bounding boxes.
 * 
 * IoU is a standard metric used to evaluate the overlap between two bounding boxes.
 * It is defined as the ratio between the area of intersection and the area of union:
 * 
 *        IoU = Area(A ∩ B) / Area(A ∪ B)
 * 
 * The result ranges from 0.0 (no overlap) to 1.0 (perfect overlap).
 * 
 * This function handles partial and non-overlapping boxes by clamping negative intersection to zero.
 * 
 * @param a First bounding box.
 * @param b Second bounding box.
 * @return float IoU value in range [0.0, 1.0].
 */
float compute_iou(const HailoBBox &a, const HailoBBox &b) {
    float x1 = std::max(a.xmin(), b.xmin());
    float y1 = std::max(a.ymin(), b.ymin());
    float x2 = std::min(a.xmax(), b.xmax());
    float y2 = std::min(a.ymax(), b.ymax());

    float inter_width = std::max(0.0f, x2 - x1);
    float inter_height = std::max(0.0f, y2 - y1);
    float inter_area = inter_width * inter_height;

    float area_a = a.width() * a.height();
    float area_b = b.width() * b.height();

    return inter_area / (area_a + area_b - inter_area);
}

/**
 * @brief Applies Non-Maximum Suppression (NMS)-like filtering based on IoU to remove redundant overlapping plates.
 * 
 * Given a list of candidate license plate detections, this function keeps the largest plates
 * and discards others that overlap significantly (based on a given IoU threshold). 
 * The function modifies the output vector `out_suppressed` with the set of suppressed (discarded) detections,
 * so they can be later removed from their original ROI.
 * 
 * Steps:
 *  - Sort all plates descendingly by area (width × height).
 *  - For each plate, if not already suppressed:
 *     - Compare it to all smaller plates.
 *     - If the IoU is greater than the specified threshold, mark the smaller plate for suppression.
 *     - Keep the larger one.
 * 
 * @param plates Vector of PlateCandidate objects containing bbox, confidence, and HailoDetectionPtr.
 * @param iou_threshold IoU threshold above which one of the overlapping plates is discarded.
 *                      Typically a value between 0.3 and 0.7 (e.g., 0.5).
 * @param out_suppressed Output vector to store HailoDetectionPtr of all suppressed (discarded) plates.
 * 
 * @return std::vector<PlateCandidate> Filtered list of plates that survived suppression.
 */
std::vector<PlateCandidate> suppress_overlapping_plates(std::vector<PlateCandidate>& plates, float iou_threshold, std::vector<HailoDetectionPtr>& out_suppressed)
{
    std::sort(plates.begin(), plates.end(), [](const PlateCandidate& a, const PlateCandidate& b) {
        return a.bbox.width() * a.bbox.height() > b.bbox.width() * b.bbox.height(); // keep bigger
    });

    std::vector<PlateCandidate> result;
    std::vector<bool> suppressed(plates.size(), false);

    for (size_t i = 0; i < plates.size(); ++i) {
        if (suppressed[i]) continue;
        result.push_back(plates[i]);
        for (size_t j = i + 1; j < plates.size(); ++j) {
            if (suppressed[j]) continue;
            float iou = compute_iou(plates[i].bbox, plates[j].bbox);
            if (iou > iou_threshold) {
                suppressed[j] = true;
                out_suppressed.push_back(plates[j].detection);
            }
        }
    }
    return result;
}

/**
 * @brief Converts a normalized bounding box (values in range [0,1]) to absolute pixel coordinates.
 * 
 * @param bbox The normalized bounding box to convert.
 * @param mat The image from which to derive dimensions for pixel scaling.
 * @return cv::Rect Bounding box in pixel coordinates (clamped to image bounds).
 */
cv::Rect get_pixel_bbox(const HailoBBox &bbox, const cv::Mat &mat)
{
    // Convert normalized to pixel coordinates
    int xmin = static_cast<int>(bbox.xmin() * mat.cols);
    int ymin = static_cast<int>(bbox.ymin() * mat.rows);
    int xmax = static_cast<int>(bbox.xmax() * mat.cols);
    int ymax = static_cast<int>(bbox.ymax() * mat.rows);

    // Clamp to valid pixel bounds (inclusive min, exclusive max)
    xmin = std::max(0, std::min(xmin, mat.cols - 1));
    ymin = std::max(0, std::min(ymin, mat.rows - 1));
    xmax = std::max(0, std::min(xmax, mat.cols));
    ymax = std::max(0, std::min(ymax, mat.rows));

    int width = std::max(0, xmax - xmin);
    int height = std::max(0, ymax - ymin);

    return cv::Rect(xmin, ymin, width, height);
}

/**
 * @brief Adjusts an overlay position to ensure it fits within the given image boundaries.
 * 
 * If the overlay goes out of bounds, attempts to shift it to the opposite direction
 * (e.g., from above to below the plate, or from right to left).
 * 
 * @param overlay_position Reference to the position rectangle to adjust.
 * @param base_rect The original bounding box (e.g., plate) used as anchor.
 * @param image_size The size of the destination image (cv::Mat.size()).
 * @param margin Optional margin in pixels between base_rect and overlay.
 * @return true if a valid (in-bounds) position was found or successfully adjusted.
 * @return false if no valid position could be determined.
 */
bool adjust_overlay_position_to_fit(cv::Rect &overlay_position,
                                    const cv::Rect &base_rect,
                                    const cv::Size &image_size,
                                    int margin = 10)
{
    // Attempt reposition if overlay is out of bounds vertically
    if (overlay_position.y < 0) {
        overlay_position.y = base_rect.y + base_rect.height + margin;
    }

    if (overlay_position.y + overlay_position.height > image_size.height) {
        int try_y = base_rect.y - overlay_position.height - margin;
        if (try_y >= 0) {
            overlay_position.y = try_y;
        }
    }

    // Attempt reposition if overlay is out of bounds horizontally
    if (overlay_position.x < 0) {
        overlay_position.x = 0;
    }

    if (overlay_position.x + overlay_position.width > image_size.width) {
        int try_x = image_size.width - overlay_position.width;
        if (try_x >= 0) {
            overlay_position.x = try_x;
        }
    }

    // Final check
    bool in_bounds = (overlay_position.x >= 0 && overlay_position.y >= 0 &&
                      overlay_position.x + overlay_position.width <= image_size.width &&
                      overlay_position.y + overlay_position.height <= image_size.height);

    return in_bounds;
}

/**
 * @brief Processes a license plate crop and directly draws it above the original bbox in the image.
 * 
 * - Converts the normalized bbox to pixel coordinates.
 * - Validates the bbox and crop.
 * - Scales the cropped image.
 * - Draws a green border for visualization.
 * - Positions the overlay just above the original bbox.
 * - Draws the confidence percentage above the overlay.
 * 
 * @param license_plate_box The normalized bounding box of the license plate.
 * @param hmat Shared pointer to the HailoMat containing the main image and crop logic.
 * @param crop_roi The ROI object representing the plate crop.
 * @param confidence Plate confidence score (range [0.0, 1.0]).
 */
void process_and_draw_license_plate(const HailoBBox &license_plate_box,
                                    std::shared_ptr<HailoMat> hmat,
                                    HailoROIPtr crop_roi,
                                    float confidence)
{
    cv::Mat &mat = hmat->get_matrices()[0];

    // Convert normalized bbox to absolute coordinates
    cv::Rect rect = get_pixel_bbox(license_plate_box, mat);
    if (rect.width == 0 || rect.height == 0)
    {
        if(DEBUG) std::cout << "Skipping overlay: bbox has zero area.\n";
        return;
    }

    // Get cropped image
    std::vector<cv::Mat> cropped_image_vec = hmat->crop(crop_roi);
    if (cropped_image_vec.empty())
    {
        if(DEBUG) std::cout << "Skipping overlay: no crop returned.\n";
        return;
    }

    cv::Mat cropped = cropped_image_vec[0];
    if (cropped.empty())
    {
        if(DEBUG) std::cout << "Skipping overlay: cropped image is empty.\n";
        return;
    }

    // Pre-resize small crops to minimum dimensions
    int orig_w = cropped.cols;
    int orig_h = cropped.rows;

    // If the plate is very small, resize it initially to a minimum size before scaling.
    cv::Mat resized_input;
    if (orig_w < MIN_LP_OUTPUT_WIDTH || orig_h < MIN_LP_OUTPUT_HEIGHT) {
        int target_w = std::max(orig_w, MIN_LP_OUTPUT_WIDTH);
        int target_h = std::max(orig_h, MIN_LP_OUTPUT_HEIGHT);
        if (DEBUG) std::cout << "[DEBUG] Pre-resizing small LP: " 
                            << orig_w << "x" << orig_h << " → " 
                            << target_w << "x" << target_h << std::endl;
        cv::resize(cropped, resized_input, cv::Size(target_w, target_h), 0, 0, cv::INTER_LINEAR);
    } else {
        resized_input = cropped;
    }

    // Final scaling
    cv::Mat scaled_image;
    cv::resize(resized_input, scaled_image, cv::Size(), PLATE_SCALE_FACTOR, PLATE_SCALE_FACTOR, cv::INTER_LINEAR);

    // Draw red border on scaled plate
    cv::rectangle(scaled_image,
                  cv::Point(0, 0),
                  cv::Point(scaled_image.cols - 1, scaled_image.rows - 1),
                  cv::Scalar(255, 0, 0),
                  LP_ZOOM_OVERLAY_THICKNESS);

    // Compute overlay position: horizontally centered, vertically above the original plate
    int center_x = rect.x + rect.width / 2;
    int overlay_x = center_x - scaled_image.cols / 2;
    int overlay_y = rect.y - scaled_image.rows - 15;  // 15px above the plate

    // Clamp Y to top of image
    if (overlay_y < 0)
        overlay_y = 0;

    cv::Rect overlay_position(overlay_x, overlay_y, scaled_image.cols, scaled_image.rows);

    // Attempt to adjust overlay if it's out of bounds
    if (!adjust_overlay_position_to_fit(overlay_position, rect, mat.size()))
    {
        if(DEBUG) std::cout << "[DEBUG] Skipping overlay — position out of bounds even after adjustment: "
                  << "(x=" << overlay_position.x
                  << ", y=" << overlay_position.y
                  << ", w=" << overlay_position.width
                  << ", h=" << overlay_position.height << ")\n";
        return;
    }

    if(DEBUG) std::cout << "[DEBUG] Overlay position validated: "
              << "(x=" << overlay_position.x
              << ", y=" << overlay_position.y
              << ", w=" << overlay_position.width
              << ", h=" << overlay_position.height << ")\n";

    // Apply overlay to image
    scaled_image.copyTo(mat(overlay_position));
    if(DEBUG) std::cout << "Overlay applied above plate at: "
              << "(x=" << overlay_position.x
              << ", y=" << overlay_position.y
              << ", w=" << overlay_position.width
              << ", h=" << overlay_position.height << ")\n";
}


/**
 * @brief Validates if the license plate bounding box overlaps sufficiently with the vehicle bounding box.
 * 
 * @param lp_bbox License plate bounding box (flattened)
 * @param vehicle_bbox Vehicle bounding box (flattened)
 * @param threshold Minimum required overlap ratio (e.g., 0.80)
 * @param vehicle_id Vehicle index (used for debug logging)
 * @return true if overlap is above threshold
 * @return false otherwise
 */
bool has_sufficient_overlap(const HailoBBox& lp_bbox, const HailoBBox& vehicle_bbox, float threshold, int vehicle_id)
{
    float inter_xmin = std::max(lp_bbox.xmin(), vehicle_bbox.xmin());
    float inter_ymin = std::max(lp_bbox.ymin(), vehicle_bbox.ymin());
    float inter_xmax = std::min(lp_bbox.xmax(), vehicle_bbox.xmax());
    float inter_ymax = std::min(lp_bbox.ymax(), vehicle_bbox.ymax());

    float inter_area = std::max(0.0f, inter_xmax - inter_xmin) * std::max(0.0f, inter_ymax - inter_ymin);
    float lp_area = lp_bbox.width() * lp_bbox.height();
    float overlap_ratio = inter_area / lp_area;

    if (overlap_ratio < threshold)
    {
        if(DEBUG) std::cout << "Discarding LP (vehicle id=" << vehicle_id << ") with overlap "
                  << static_cast<int>(overlap_ratio * 100) << "% < threshold ("
                  << static_cast<int>(threshold * 100) << "%)" << std::endl;
        return false;
    }

    return true;
}

/**
 * @brief Post-processes vehicle and license plate detections.
 * 
 * For each vehicle detection, finds the best-matching license plate (based on confidence and spatial overlap),
 * and immediately draws the license plate crop onto the main image. Overlays are centered and scaled appropriately.
 * 
 * Steps:
 *  - Iterates over each vehicle detection.
 *  - For each vehicle, gathers nested license plate detections.
 *  - Filters out LPs that do not meet the minimum overlap threshold with their vehicle.
 *  - Selects the highest-confidence valid plate per vehicle.
 *  - Applies the plates overlay.
 * 
 * @param roi HailoROIPtr containing vehicle and nested license plate detections.
 * @param hmat Shared pointer to the image data on which overlays are drawn.
 */
void lpr_postprocess(HailoROIPtr roi, std::shared_ptr<HailoMat> hmat)
{
    if (!roi)
        return;

    if(DEBUG) std::cout << "==================== LPR Post-Process ====================" << std::endl;

    auto vehicle_detections = hailo_common::get_hailo_detections(roi);
    int vehicle_counter = 0;
    int lp_counter = 0;

    std::vector<PlateCandidate> candidates;

    for (auto &vehicle : vehicle_detections)
    {
        auto vehicle_bbox = hailo_common::create_flattened_bbox(vehicle->get_bbox(), vehicle->get_scaling_bbox());
        auto lp_detections = hailo_common::get_hailo_detections(vehicle);
        std::vector<HailoDetectionPtr> to_remove;

        if(DEBUG) std::cout << "vehicle: #" << vehicle_counter << ", confidence=" << vehicle->get_confidence() << std::endl;

        for (auto &lp : lp_detections)
        {
            float lp_confidence = lp->get_confidence();
            if(DEBUG) std::cout << "plate: #" << lp_counter << ", confidence=" << lp_confidence << std::endl;

            lp_counter++;

            auto lp_bbox = hailo_common::create_flattened_bbox(lp->get_bbox(), lp->get_scaling_bbox());

            float lp_area = lp_bbox.width() * lp_bbox.height();
            if (lp_area < MIN_LP_AREA) {
                if (DEBUG) std::cout << "Discarding LP due to small area: " << lp_area << " < " << MIN_LP_AREA << std::endl;
                to_remove.push_back(lp);
                continue;
            }

            // Skip LPs that do not sufficiently overlap with the vehicle
            if (!has_sufficient_overlap(lp_bbox, vehicle_bbox, LP_OVERLAP_THRESHOLD, vehicle_counter)){
                to_remove.push_back(lp);
                continue;
            }

            candidates.push_back({lp, lp_bbox, lp_confidence});
        }

        // Remove plates that are inside of other plates keeping the bigger plates
        auto survivors = suppress_overlapping_plates(candidates, PLATES_OVERLAP_THRESHOLD, to_remove);

        // Draw the survivor plates
        for (const auto& plate : survivors) {
            process_and_draw_license_plate(plate.bbox, hmat, plate.detection, plate.confidence);
        }

        // Remove the thrash plates from the original hailo detections to avoid drawing the bboxes
        if (!to_remove.empty())
            hailo_common::remove_detections(vehicle, to_remove);

        ++vehicle_counter;
    }
}

// Entry point
void filter(HailoROIPtr roi, GstVideoFrame *frame)
{
    auto hmat = get_mat_by_format(*(&frame->buffer), &frame->info, 1, 1);
    lpr_postprocess(roi, hmat);
}

/**
 * @brief Extracts vehicle crops from ROI and logs raw detection info.
 * 
 * @param image The input image from which detections were generated.
 * @param roi The parent ROI containing vehicle detections.
 * @return std::vector<HailoROIPtr> Vector of individual vehicle detection ROIs.
 */
std::vector<HailoROIPtr> crop_vehicles(std::shared_ptr<HailoMat> image, HailoROIPtr roi)
{
    std::vector<HailoROIPtr> crop_rois;

    if(DEBUG) std::cout << "==================== CROP VEHICLES ====================" << std::endl;

    // Get all detections from the ROI
    std::vector<HailoDetectionPtr> detections_ptrs = hailo_common::get_hailo_detections(roi);

    if(DEBUG) std::cout << "Detected " << detections_ptrs.size() << " objects." << std::endl;

    int index = 0;
    for (const auto& detection : detections_ptrs)
    {
        const HailoBBox& bbox = detection->get_bbox();

        if(DEBUG) std::cout << "Vehicle #" << index
                  << " | Label: \"" << detection->get_label()
                  << "\", ClassID: " << detection->get_class_id()
                  << ", Confidence: " << detection->get_confidence()
                  << ", BBox: [x=" << bbox.xmin()
                  << ", y=" << bbox.ymin()
                  << ", w=" << bbox.width()
                  << ", h=" << bbox.height()
                  << "]" << std::endl;

        crop_rois.emplace_back(detection);
        ++index;
    }
    return crop_rois;
}
