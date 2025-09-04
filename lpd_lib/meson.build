project('gst-hailo-tools', ['c', 'cpp'],
  version : '3.31.0',
  default_options : ['buildtype=release', 'c_std=c11', 'cpp_std=c++17']
)

tappas_dir = get_option('tappas_dir')
if tappas_dir == ''
  error('The option -Dtappas_dir=/path/to/tappas is required')
endif
message('Tappas dir: ' + tappas_dir)

install_dir = get_option('install_dir')
if install_dir == ''
  error('The option -Dinstall_dir=/path/to/install/app is required')
endif
message('Install dir: ' + install_dir)

tappas_core_dir     = join_paths(tappas_dir, 'core')
tappas_hailo_dir    = join_paths(tappas_core_dir, 'hailo')
tappas_general_dir  = join_paths(tappas_hailo_dir, 'general')
tappas_plugins_dir  = join_paths(tappas_hailo_dir, 'plugins')
tappas_common_dir   = join_paths(tappas_plugins_dir, 'common')

image_src        = join_paths(tappas_common_dir,   'image.cpp')
cv_singleton_src = join_paths(tappas_general_dir,  'hailo_cv_singleton.cpp')
lpr_postprocess_source = 'src/lpr_postprocess.cpp'

compiler = meson.get_compiler('cpp')
compiler_version_major = compiler.version().split('.')[0].to_int()
if compiler_version_major >= 9
  message('GCC >= 9 detected; adding extra warnings')
  add_global_arguments('-Wpessimizing-move', language : 'cpp')
  add_global_arguments('-Wredundant-move',  language : 'cpp')
  add_global_arguments('-fconcepts',        language : 'cpp')
endif

inc_core      = include_directories(tappas_core_dir)
inc_hailo     = include_directories(tappas_hailo_dir)
inc_plugins   = include_directories(tappas_plugins_dir)
inc_common    = include_directories(tappas_common_dir)
inc_general   = include_directories(tappas_general_dir)
inc_local     = include_directories('src', 'src')

all_incs = [inc_core, inc_hailo, inc_plugins, inc_common, inc_general, inc_local]

gst_req       = '>= 1.0.0'
gst_dep       = dependency('gstreamer-1.0',       version : gst_req, fallback : ['gstreamer', 'gst_dep'])
gst_base_dep  = dependency('gstreamer-base-1.0',  version : gst_req, fallback : ['gstreamer', 'gst_base_dep'])
gst_app_dep   = dependency('gstreamer-app-1.0',   version : gst_req, fallback : ['gstreamer', 'gst_app_dep'])
gstvideo_dep  = dependency('gstreamer-video-1.0', version : gst_req, fallback : ['gst-plugins-base', 'video_dep'])
opencv_dep    = dependency('opencv4', version : '>= 4.0', method : 'pkg-config')
thread_dep    = dependency('threads')

plugin_deps = [gst_dep, gst_base_dep, gstvideo_dep, gst_app_dep]

image_lib = shared_library('hailo_gst_image',
  image_src,
  include_directories : all_incs,
  dependencies        : plugin_deps + [opencv_dep, thread_dep],
  gnu_symbol_visibility : 'default',
  version             : meson.project_version(),
  install             : true,
  install_dir         : install_dir,
)

image_dep = declare_dependency(
  include_directories : [inc_core, inc_hailo, inc_plugins, inc_common, inc_general],
  link_with           : image_lib
)

cv_singleton_lib = shared_library('hailo_cv_singleton',
  cv_singleton_src,
  include_directories : all_incs,
  dependencies        : [opencv_dep, thread_dep, image_dep] + plugin_deps,
  gnu_symbol_visibility : 'default',
  version             : meson.project_version(),
  install             : true,
  install_dir         : install_dir,
)

cv_singleton_dep = declare_dependency(
  include_directories : [inc_core, inc_hailo, inc_plugins, inc_common, inc_general],
  link_with           : cv_singleton_lib
)

lpr_postprocess_lib = shared_library('lpr_postprocess',
  lpr_postprocess_source,
  include_directories : all_incs,
  dependencies        : plugin_deps + [opencv_dep, thread_dep, cv_singleton_dep, image_dep],
  gnu_symbol_visibility : 'default',
  install             : true,
  install_dir         : install_dir,
)
