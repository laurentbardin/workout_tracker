if (typeof window.ot === 'undefined') {
    console.error('Missing global object "ot". Is Oat loaded properly?');
}

function notifySuccess(evt) {
    ot.toast(evt.detail.value, 'Success', { placement: 'top-center', variant: 'success', duration: 2500 });
}

export { notifySuccess };
