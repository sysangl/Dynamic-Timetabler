
/**
 *  Fetches all timetable items (unfiltered)
 * 
 */
async function fetchPayload() {
    const response = await fetch('/server/timetable', {
        method : 'GET'
    });

    if (!response.ok) {
        throw new Error(`${response.status} ${response.statusText}`)
    }
    return response.json()
}

const popupMenu = document.getElementById('popup-menu');
const container = document.getElementById('tt-schedule-container')
const backdrop  = document.getElementById('backdrop')

/**
 * 
 * @param {HTMLDivElement} target 
 * @returns 
 */
function showPopupMenu(target) {
    const alreadyOpen = popupMenu.classList.contains('open') && target === popupMenu._currentTarget;
    if (alreadyOpen) {
        closePopupMenu();
        return;
    }
    const bRect = target.getBoundingClientRect()
    popupMenu.style.top = `${bRect.bottom + window.scrollY}px`;
    popupMenu.style.left = `${bRect.left + window.scrollX}px`;
    popupMenu._currentTarget = target;
    popupMenu.classList.add('open');
    backdrop.classList.add('active');
}

function closePopupMenu() {
    popupMenu.classList.remove('open');
    backdrop.classList.remove('active');
    if (popupMenu._currentTarget) {
        delete popupMenu._currentTarget
    }
}

container.addEventListener('click', (e)=>{
    const block = e.target.closest('.timetable-block');
    if (!block) return;
    e.stopPropagation();
    showPopupMenu(block);
})

backdrop.addEventListener('click', closePopupMenu)

document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape' && popupMenu.classList.contains('open')) {
    closePopupMenu();
  }
});

async function deleteBlock() {
    const block = popupMenu._currentTarget
    const blockId = block.dataset.blockId
    block.remove()
    console.log(`Deleting block ${blockId}`)
    const response = await fetch(`/server/timetable/blocks/${blockId}`,{
        'method' : 'DELETE'
    })
    closePopupMenu();
}

function editBlock() {
    console.log("Edit")
}

function completeBlock() {
    console.log("complete")
}

function markRescheduleBlock() {
    console.log('mark resc')
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
    el.dataset.blockId = block.id;

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

        if (endMins > minsInDay + scheduleEndMins) {
            const nextDayIdx = (dayIdx + 1) % 7;
            const overflowMins = endMins - minsInDay;
            const overflowEl = buildPieceElement(block,scheduleEndMins,overflowMins-scheduleEndMins,tl);
            pieces.push({dayIdx: nextDayIdx, el: overflowEl})
        }

    }
    return pieces
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
window.addEventListener('resize', closePopupMenu);
window.addEventListener('scroll', closePopupMenu);