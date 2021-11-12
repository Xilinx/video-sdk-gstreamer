gstvvas_xlookahead = library('gstvvas_xlookahead', ['gstvvas_xlookahead.c', 'la_algo/xlnx_aq_core.c', 'la_algo/xlnx_rc_aq.c', 'la_algo/xlnx_spatial_aq.c', 'la_algo/xlnx_queue.c'],
  c_args : gst_plugins_vvas_args,
  include_directories : [configinc, libsinc],
  dependencies : [gstvideo_dep, gst_dep, gstvvasalloc_dep, xrt_dep, gstallocators_dep, uuid_dep, vvasutils_dep, gstvvaslameta_dep, xrm_dep],
  install : true,
  install_dir : plugins_install_dir,
)

pkgconfig.generate(gstvvas_xlookahead, install_dir : plugins_pkgconfig_install_dir)
plugins += [gstvvas_xlookahead]
