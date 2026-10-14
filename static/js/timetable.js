async function fetchPayload() {
    const response = await fetch('/server/timetable', {
        method : 'GET',
        headers: {
            'Accept': 'application/json'
        }
    });

    if (!response.ok) {
        throw new Error(`${response.status} ${response.statusText}`)
    }
    return response.json()
}


/**
 * Turns a block into an element
 * ONLY for timetable blocks
 * 
 * @param {Object} block
 * @returns {HTMLDivElement} 
 */
function makeBlockElement(block) {
    const start = new Date(block.start_datetime);
    const end = new Date(block.end_datetime);

    // days were misaligned by -1 in the previous script.
    // so we normalise the day index
    // Mon : 0 -> Sun : 6
    const dayIdx = (start.getDay() + 6 ) % 7; 

    // i had a really messy way of calculating the offset for each block, but it worked
    // this is just more refined
    const minsInDay = 24 * 60;
    const startMins = start.getHours() * 60 + start.getMinutes();
    const endMins = end.getHours() * 60 + end.getMinutes();

    // another prbolem was if the length of the block went over midnight or the starting hour of the timetable
    // this is just to fix the midnight problem, just add 24h if it goes over
    const timeLength = (endMins - startMins) >= 0 ? (endMins - startMins) : (endMins + minsInDay - startMins)
    // and this is to fix spillover
    const scheduleStartMins = window.settings['start_hour'] * 60;
    const effectiveStart = startMins - scheduleStartMins

    const tl = document.getElementById('tt-topbar-timeline');
    console.log(`sm: ${startMins}`)
    console.log(`ss: ${scheduleStartMins}`)
    const leftPx = (effectiveStart / minsInDay) * tl.scrollWidth;
    const widthPx = (timeLength / minsInDay) * tl.scrollWidth;

    // building the actual elem
    const el = document.createElement('div');
    el.className = 'timetable-block';
    el.id = `timetable-block-${block.id}`;
    el.style.setProperty('--left', `${leftPx}px`);
    el.style.setProperty('--width', `${widthPx}px`);
    el.style.setProperty('--bg-colour', block.colour);

    const titleSpan = document.createElement('span');
    titleSpan.className = 'block-title';
    titleSpan.textContent = block.title;

    const timeSpan = document.createElement('span');
    timeSpan.className = 'block-time';
    timeSpan.textContent = `${formatTime(start.getHours())}:${formatTime(start.getMinutes())} - ${formatTime(end.getHours())}:${formatTime(end.getMinutes())}`

    el.append(titleSpan, document.createElement('br'), timeSpan);
    el.dataset.dayIdx = dayIdx;
    return {dayIdx, el};
}

async function renderTimetable() {
    const payload = await fetchPayload();
    const blocks = payload.blocks;
    const dayContainers = Array.from({ length: 7 }, (_, i) => {
        // The DOM has: <section id="day-container-Mon"><div class="day-inner"></div></section>
        const container = document.getElementById(`day-container-${['Mon','Tue','Wed','Thu','Fri','Sat','Sun'][i]}`);
        return container;
    });

    const fragments = Array.from({length: 7}, () => document.createDocumentFragment());

    for (const block of blocks) {
        const {dayIdx, el} = makeBlockElement(block);
        fragments[dayIdx].appendChild(el);
    }

    fragments.forEach((frag, i)=>{
        if (frag.childElementCount) {
            dayContainers[i].appendChild(frag);
        }
    })
}

renderTimetable().catch(err => console.error('Timetable render failed:', err))