const calendar = window.calendar || (window.calendar = {});

calendar.navigate = function(key) {
    let anchor;

    if (key == 'ArrowLeft') {
        anchor = htmx.find('a#previous-month')
    } else if (key == 'ArrowRight') {
        anchor = htmx.find('a#next-month')
    } else {
        return;
    }

    if (!anchor) {
        console.error('Navigation anchor not found');
    } else {
        anchor.click();
    }
}

document.body.addEventListener('keyup', (ev) => calendar.navigate(ev.key));
