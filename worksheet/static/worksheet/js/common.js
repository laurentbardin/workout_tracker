(function(w) {
    if (typeof w.notifySuccess != 'undefined') {
        console.warn('window.notifySuccess() already defined');
        return;
    }

    function notifySuccess(msg, duration=2500) {
        ot.toast(msg, 'Success', { placement: 'top-center', variant: 'success', duration: duration });
    }

    function notifyWarning(msg, duration=4000) {
        ot.toast(msg, 'Warning', { placement: 'top-center', variant: 'warning', duration: duration });
    }

    function notifyError(msg, duration=4000) {
        ot.toast(msg, 'Error', { placement: 'top-center', variant: 'danger', duration: duration });
    }

    w.notifySuccess = notifySuccess
    w.notifyWarning = notifyWarning
    w.notifyError = notifyError
})(window);
