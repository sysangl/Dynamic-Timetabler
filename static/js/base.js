/**
 * Toggles the sidebar
 */
function toggleSidebar() {
    const sidebar = document.getElementById('sidebar');
    const container = document.getElementById('content');
    const ham = document.querySelector('.ham');

    sidebar.classList.toggle('expanded');
    container.classList.toggle('pushed');
    ham.classList.toggle('active');
}

document.querySelectorAll('.sidebar-btn').forEach(b => b.classList.toggle('active', b.dataset.page===initialPage))

/**
 * Fetches the supplied user's settings. If not supplied, defaults to 1.
 * If settings have already been fetched, use cache settings.
 * @param {number} userId 
 * @returns {JSON}
 */
async function fetchSettings() {
    if (window.settings == null) {
        try {
            console.log("Attempting to fetch settings")
            const response = await fetch(`http://localhost:58362/api/users/settings`, {
                method: 'GET',
                headers: {
                    'Accept' : 'application/json'
                },
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status} - ${response.statusText}`);
            }

            const data = await response.json();
            window.settings = data["settings"];
            return data["settings"];
        } catch (err) {
            console.error('Failed to fetch settings JSON:', err);
            throw err;
        }
    } else {
        console.log("Using cached settings")
        return window.settings;
    }

}

document.addEventListener('fragmentloaded', e => {
    const page = e.detail.page;          // e.g. "settings"
    const registry = window.pageInits || {};

    if (typeof registry[page] === 'function') {
        // Call the init routine that the fragment has registered
        registry[page]();
    } else {
        // console.warn(`No init function registered for page "${page}"`);
    }

    window.pageIntervals.temporary.forEach(i => clearInterval(i))

});

function clearFragmentInterval(name) {
    clearInterval(window.pageIntervals.persistent[name]);
}


(async () => {window.settings = await fetchSettings(1);});
window.pageIntervals = window.pageIntervals || {};
window.pageIntervals.temporary = window.pageIntervals.temporary || [];
window.pageIntervals.persistent = window.pageIntervals.persistent || {};
window.pageInits = window.pageInits || {};