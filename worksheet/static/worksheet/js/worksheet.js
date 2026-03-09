(function(w) {
    if (typeof w.worksheet != 'undefined') {
        console.warn('window.worksheet already defined');
        return;
    }

    function checkInput (elt, _ev) {
        elt.value = elt.value.trim();
        if (!elt.checkValidity()) {
            elt.reportValidity();
        }
    }

    function updateClock(elt, start) {
        const start_date = new Date(start);
        if (isNaN(start_date.getTime())) {
            console.warn('Cannot setup clock: invalid date', start);
            return;
        }

        const clock = htmx.find(elt)
        if (!clock) {
            console.warn(`Cannot setup clock: element ${elt} not found`, start);
            return;
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

            htmx.swap(clock, values.join(':'), {swapStyle: 'innerHtml'});
        }
    }

    function initClock(start) {
        const update = updateClock('#clock', start);
        if (update) {
            update();
            htmx.removeClass('#clock', 'hidden');
            setInterval(update, 1000);
        }
    }

    function showNotePopover(source) {
        const popover = htmx.find('#notePopover');
        if (!popover) {
            console.error('Cannot toggle popover: element not found');
            return;
        }

        const form = htmx.find(popover, '#noteForm');
        if (!form) {
            console.error('Cannot initialise note form: element not found');
            return;
        }

        form.action = source.dataset.actionUrl;
        form.setAttribute('hx-post', form.action);

        htmx.process(form);

        const input = htmx.find(form, 'input[name="note"]');
        if (!input) {
            console.warn('Cannot set input value: element not found');
        } else {
            input.value = source.dataset.note;
        }

        popover.show();
    }

    w.worksheet = {
        checkInput: checkInput,
        initClock: initClock,
        showNotePopover: showNotePopover,
    };
})(window);
