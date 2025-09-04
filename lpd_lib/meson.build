project('gst-hailo-tools', ['c', 'cpp'],
  version : '3.31.0',
  default_options : ['buildtype=release', 'c_std=c11', 'cpp_std=c++17']
)

lpr_postprocess_source = 'src/lpr_postprocess.cpp'

compiler = meson.get_compiler('cpp')
compiler_version_major = compiler.version().split('.')[0].to_int()
if compiler_version_major >= 9
  message('GCC >= 9 detected; adding extra warnings')
  add_global_arguments('-Wpessimizing-move', language : 'cpp')
  add_global_arguments('-Wredundant-move',  language : 'cpp')
  add_global_arguments('-fconcepts',        language : 'cpp')
endif

gst_req       = '>= 1.0.0'
gst_dep       = dependency('gstreamer-1.0',       version : gst_req, fallback : ['gstreamer', 'gst_dep'])
gst_base_dep  = dependency('gstreamer-base-1.0',  version : gst_req, fallback : ['gstreamer', 'gst_base_dep'])
gst_app_dep   = dependency('gstreamer-app-1.0',   version : gst_req, fallback : ['gstreamer', 'gst_app_dep'])
gstvideo_dep  = dependency('gstreamer-video-1.0', version : gst_req, fallback : ['gst-plugins-base', 'video_dep'])
opencv_dep    = dependency('opencv4', version : '>= 4.0', method : 'pkg-config')
thread_dep    = dependency('threads')

plugin_deps = [gst_dep, gst_base_dep, gstvideo_dep, gst_app_dep]

tappas_dep = dependency('hailo_tappas')

lpr_postprocess_lib = shared_library('lpr_postprocess',
  lpr_postprocess_source,
  dependencies        : [plugin_deps, tappas_dep],
  gnu_symbol_visibility : 'default',
  install             : true
)
