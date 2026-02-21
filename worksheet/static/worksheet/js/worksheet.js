const worksheet = window.worksheet || (window.worksheet = {})

worksheet.checkInput = function(elt, _ev) {
    elt.value = elt.value.trim();
    if (!elt.checkValidity()) {
        elt.reportValidity();
    }
}

worksheet.updateClock = function(elt, start) {
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

worksheet.initClock = function(start) {
    const update = worksheet.updateClock('#clock', start);
    update();
    htmx.removeClass('#clock', 'hidden');
    setInterval(update, 1000);
}

worksheet.initNoteForm = function(actionUrl, fromButton) {
    const form = htmx.find('#noteForm');
    if (!form) {
        console.error('Cannot initialise note form: element not found');
        return;
    }
    form.action = actionUrl;
    form.setAttribute('hx-post', form.action);

    htmx.process(form);

    const input = htmx.find(form, 'input[name="note"]');
    if (!input) {
        console.warn('Cannot set input value: element not found');
    } else {
        input.value = fromButton.dataset.note;
    }
}

worksheet.watchIcon = function(records, _observer) {
    records.filter(r => r.addedNodes.length > 0).forEach(r => {
        r.addedNodes.forEach(el => {
            el.querySelectorAll('[title]').forEach(el => {
                const text = el.getAttribute('title');
                if (text) {
                    el.setAttribute('data-tooltip', text);
                    if (!el.hasAttribute('aria-label')) {
                        el.setAttribute('aria-label', text);
                    }
                    el.removeAttribute('title');
                }
            });
        });
    })
}
const observer = new MutationObserver(worksheet.watchIcon);
document.querySelectorAll('section.worksheet .result.action').forEach(el => {
    observer.observe(el, { childList: true });
});
