const contentDiv = document.getElementById('content');
const buttons = document.querySelectorAll('.sidebar-btn');

/**
 * Helper function. Loads a page fragment and pushes it to #content
 * @param {string} page 
 * @param {boolean} push 
 * @returns 
 */
async function loadPage(page, push = true) {
    if(!['timetable','settings','management'].includes(page)) page = 'unknown';
    if(currentPage==page) return;

    // getch fragment 
    const response = await fetch(`/app/page/${page}`, {
        headers: { 'X-Requested-With': 'XMLHttpRequest' }
    });

    if (!response.ok) {
        console.error(`Failed to load ${page}`, response.status);
        return;
    }

    // clear intervals and event listeners
    window.pageIntervals.temporary.forEach(i => clearInterval(i))
    const eventListeners = window.eventListeners.temporary;
    for (const [element, type, listener] of eventListeners) {
        element.removeEventListener(type, listener)
    }
    // replace view
    const html = await response.text();
    contentDiv.innerHTML = html;

    const scripts = contentDiv.querySelectorAll('script');

    for (const oldScript of scripts) {

        const newScript = document.createElement('script');

        // copy all attributes
        for (const attr of oldScript.attributes) {
            newScript.setAttribute(attr.name, attr.value);
        }

        // make script syncronous
        newScript.async = false;

        if (!oldScript.src) {
            newScript.textContent = oldScript.textContent;
        }

        // replace script and retrigger
        oldScript.parentNode.replaceChild(newScript, oldScript);
    }

    contentDiv.dispatchEvent(new CustomEvent('fragmentloaded', {
        bubbles: true,
        detail: { page: page }
    }));

    currentPage = page

    // update nav buttoms
    buttons.forEach(b => b.classList.toggle('active', b.dataset.page === page));

    // push entry (new url)
    if (push) {
        const url = page === 'timetable' ? '/app/timetable' : `/app/${page}`;
        history.pushState({ page }, '', url);
    }


}

// button listener (handles clicks)
buttons.forEach(btn => {
    btn.addEventListener('click', e => {
        const targetPage = btn.dataset.page;
        loadPage(targetPage);
    });
});

// back/forward navigation from browser buttons
window.addEventListener('popstate', e => {
    const page = e.state?.page || location.pathname.replace(/^\//,'') || 'home';
    loadPage(page, false); // dont push new history
});

// direct page navigation
// we make sure to have the correct history for button navigation (back-button)
window.addEventListener('load', () => {
    const initialPage = location.pathname.replace(/^\//, '') || 'home';
    history.replaceState({ page: initialPage},'');
});
