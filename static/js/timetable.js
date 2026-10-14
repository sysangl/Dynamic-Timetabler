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
 * 
 * @param {Object} block 
 * @param {number} startMins 
 * @param {number} lengthMins 
 * @param {HTMLDivElement} tl
 * @returns {HTMLDivElement}
 */
function buildPieceElement(block, startMins, lengthMins, tl) {
    const start = new Date(block.start_datetime);
    const end = new Date(block.end_datetime);
    const minsInDay = 24 * 60;
    const scheduleStartMins = (window.settings?.start_hour ?? 0) * 60;
    const effectiveStart = startMins - scheduleStartMins;
    const leftPx = (effectiveStart/minsInDay) * tl.scrollWidth;
    const widthPx = (lengthMins/minsInDay) * tl.scrollWidth;

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
    return el;
}

/**
 * Turns a block into an element
 * ONLY for timetable blocks
 * Splits the block if it extends past the visible space
 * 
 * @param {Object} block
 * @returns {Array<{dayIdx:number, el:HTMLDivElement}} 
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
    var endMins = end.getHours() * 60 + end.getMinutes();
    if (endMins <= startMins) endMins += minsInDay;

    const scheduleStartMins = (window.settings?.start_hour ?? 0) * 60;
    const scheduleEndMins = ((window.settings?.start_hour ?? 0)%24) * 60;
    
    const tl = document.getElementById('tt-topbar-timeline');
    const pieces = [];

    // if the block starts before the visible space
    if (startMins < scheduleStartMins) {
        // normalise idx for the previous day
        const prevDayidx = (dayIdx - 1 + 7) % 7
        const prevLength = Math.min(scheduleStartMins, endMins) - startMins;
        if (prevLength > 0) {
            const prevEl = buildPieceElement(block,minsInDay+startMins,prevLength, tl);
            pieces.push({dayIdx: prevDayidx, el:prevEl});
        }

        const remainingStart = scheduleStartMins;
        const remainingLength = endMins - scheduleStartMins;
        if (remainingLength > 0) {
            const currentEl = buildPieceElement(block, remainingStart, remainingLength, tl);
            pieces.push({dayIdx: dayIdx, el: currentEl})
        }
    } else {
        const currentStart = Math.max(startMins, scheduleStartMins);
        const currentEnd = Math.min(endMins, minsInDay + scheduleEndMins);
        const currentLength = currentEnd - currentStart;

        if (currentLength > 0) {
            const currentEl = buildPieceElement(block, currentStart, currentLength, tl);
            pieces.push({dayIdx: dayIdx, el:currentEl});
        }

        if (endMins > scheduleEndMins) {
            const nextDayIdx = (dayIdx + 1) % 7;
            const overflowMins = endMins - minsInDay;
            const overflowEl = buildPieceElement(block,scheduleEndMins,overflowMins-scheduleEndMins,tl);
            pieces.push({dayIdx: nextDayIdx, el: overflowEl})
        }

    }
    console.log(pieces)
    return pieces


    // const effectiveStart = startMins - scheduleStartMins
    // const timeLength = (endMins - startMins) >= 0 ? (endMins - startMins) : (endMins + minsInDay - startMins)

    // const leftPx = (effectiveStart / minsInDay) * tl.scrollWidth;
    // const widthPx = (timeLength / minsInDay) * tl.scrollWidth;

    // // building the actual elem
    // const el = document.createElement('div');
    // el.className = 'timetable-block';
    // el.id = `timetable-block-${block.id}`;
    // el.style.setProperty('--left', `${leftPx}px`);
    // el.style.setProperty('--width', `${widthPx}px`);
    // el.style.setProperty('--bg-colour', block.colour);

    // const titleSpan = document.createElement('span');
    // titleSpan.className = 'block-title';
    // titleSpan.textContent = block.title;

    // const timeSpan = document.createElement('span');
    // timeSpan.className = 'block-time';
    // timeSpan.textContent = `${formatTime(start.getHours())}:${formatTime(start.getMinutes())} - ${formatTime(end.getHours())}:${formatTime(end.getMinutes())}`

    // el.append(titleSpan, document.createElement('br'), timeSpan);
    // el.dataset.dayIdx = dayIdx;
    // return {dayIdx, el};
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
        const pieces = makeBlockElement(block);
        // fragments[dayIdx].appendChild(el);
        for (const {dayIdx, el} of pieces) {
            console.log(`appending child to dayIdx ${dayIdx}`)
            fragments[dayIdx].appendChild(el);
        }
    }

    fragments.forEach((frag, i)=>{
        if (frag.childElementCount) {
            dayContainers[i].appendChild(frag);
        }
    })
}

renderTimetable().catch(err => console.error('Timetable render failed:', err))