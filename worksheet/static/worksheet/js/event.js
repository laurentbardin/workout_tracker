function registerEvents(list) {
    list.forEach((data) => registerEvent(data));
}

function registerEvent(data) {
    let elt;

    if (!data.element) {
        elt = document;
    } else {
        elt = htmx.find(data.element);
        if (!elt) {
            console.error(`Could not register event: element ${data.element} not found`);
            console.info('Event data', data);
            return;
        }
    }

    elt.addEventListener(data.event, data.cb);
}
