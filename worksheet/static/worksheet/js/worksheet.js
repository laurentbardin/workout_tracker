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

    clock = {
        selector: '#clock',
        elt: undefined,
        startTime: undefined,
    };

    function initClock() {
        clock.elt = htmx.find(clock.selector)
        if (!clock.elt) {
            console.warn(`Cannot setup clock: element ${clock.selector} not found`);
            return;
        }

        clock.startTime = new Date(clock.elt.dataset.startedAt);
        if (isNaN(clock.startTime)) {
            console.warn('Cannot setup clock: invalid date', clock.elt.dataset.startedAt);
            return;
        }

        updateClock();
        htmx.removeClass('#clock', 'hidden');
        setInterval(updateClock, 1000);
    }

    function updateClock() {
        // Discard milliseconds
        let duration = Math.floor((new Date() - clock.startTime) / 1000);

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

        htmx.swap(clock.elt, values.join(':'), {swapStyle: 'innerHtml'});
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

    function updateSuccess(evt) {
        const e = evt.target.parentElement;
        htmx.removeClass(e, 'error');
        htmx.addClass(e, 'success');

        if (evt.detail.meter.value) {
            htmx.find('#worksheet-progress').value = evt.detail.meter.value;
        }
    }

    function updateError(evt) {
        const e = evt.target.parentElement;
        htmx.removeClass(e, 'success');
        htmx.addClass(e, 'error');
    }

    function notifySuccess(evt) {
        w.notifySuccess(evt.detail.value)
    }

    w.worksheet = {
        checkInput: checkInput,
        initClock: initClock,
        showNotePopover: showNotePopover,
        updateSuccess: updateSuccess,
        updateError: updateError,
        notifySuccess: notifySuccess,
    };
})(window);
