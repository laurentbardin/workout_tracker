function checkInput(elt, _ev) {
    elt.value = elt.value.trim();
    if (!elt.checkValidity()) {
        elt.reportValidity();
    }
}
document.checkInput = checkInput;

function updateClock(elt, start) {
    const start_date = new Date(start);
    if (isNaN(start_date.getTime())) {
        console.warn('Invalid date', start);
        return function() {};
    }

    return function() {
        // Discard milliseconds
        let duration = Math.floor((new Date() - start_date) / 1000);

        // Extract the number of seconds and minutes
        const values = [];
        const units = [60, 60];
        units.forEach((u) => {
            values.push(String(duration % u).padStart(2, '0'));
            duration = Math.floor(duration / u);
        })

        // Only the number of hours remain in duration
        values.push(duration);
        values.reverse();

        htmx.swap(elt, values.join(':'), {swapStyle: 'innerHtml'});
    }
}
document.updateClock = updateClock;

function initNoteForm(actionUrl, fromButton) {
    const form = htmx.find('#noteForm');
    if (!form) {
        console.error('Cannot initialise note form: element not found');
        return;
    }
    form.action = actionUrl;
    form.setAttribute('hx-post', form.action);
    form.setAttribute('hx-target', '#' + fromButton.id);

    htmx.process(form);

    const input = htmx.find(form, 'input[name="note"]');
    if (!input) {
        console.warn('Cannot set input value: element not found');
    } else {
        input.value = fromButton.dataset.note;
    }
}
document.initNoteForm = initNoteForm;
