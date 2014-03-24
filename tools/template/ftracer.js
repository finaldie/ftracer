var GLOBAL_msg = null;

function showQuickView(e, msg) {
    if (!e) {
        e = window.event;
    }

    if (GLOBAL_msg == null) {
        GLOBAL_msg = msg;
    }

    var clientX = e.pageX + 20;
    var clientY = e.pageY + 10;
    var quickview = document.getElementById('Quickview');
    quickview.innerHTML = GLOBAL_msg;
    quickview.style.marginTop = clientY + "px";
    quickview.style.marginLeft = clientX + "px";
    quickview.style.display = "inline";
    document.onmousemove = showQuickView;
}

function clearQuickView(e) {
    if (!e) {
        e = window.event;
    }

    var quickview = document.getElementById('Quickview');
    quickview.style.display = "none";
    GLOBAL_msg = null;
    document.onmousemove = null;
}
