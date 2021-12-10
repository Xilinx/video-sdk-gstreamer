gstvvas_xvcuenc = library('gstvvas_xvcuenc', 'gstvvas_xvcuenc.c',
  c_args : gst_plugins_vvas_args,
  include_directories : [configinc, libsinc],
  dependencies : [gstvideo_dep, gst_dep, gstvvasalloc_dep, gstvvaspool_dep, xrt_dep, dl_dep, gstallocators_dep, uuid_dep, gstvvaslameta_dep, gstvvashdrmeta_dep, vvasutils_dep, xrm_dep],
  install : true,
  install_dir : plugins_install_dir,
)

pkgconfig.generate(gstvvas_xvcuenc, install_dir : plugins_pkgconfig_install_dir)
plugins += [gstvvas_xvcuenc]
