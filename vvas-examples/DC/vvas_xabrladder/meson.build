#project('app', 'c')
src = ['src/vvas_xabrladder.c']
exe = executable('vvas_xabrladder', src,
dependencies : [gstvideo_dep, gst_dep, xrt_dep, jansson_dep, vvasutils_dep, gstpbutils_dep],
install : true,
)

install_data ('abrladder.json')
