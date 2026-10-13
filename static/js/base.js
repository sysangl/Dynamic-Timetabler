// Sidebar toggle
function toggleSidebar() {
    const sidebar = document.getElementById('sidebar');
    const container = document.getElementById('content');
    const ham = document.querySelector('.ham');

    sidebar.classList.toggle('expanded');
    container.classList.toggle('pushed');
    ham.classList.toggle('active');
}


document.querySelectorAll('.sidebar-btn').forEach(b => b.classList.toggle('active', b.dataset.page===initialPage))

var persistentSettings = null;
const settingsUrl = 'http://localhost:58362/server/user/1/settings'



// send a request to the server for the current user's settings, currently hardcoded to user 1
async function fetchSettings(userId) {
    if (persistentSettings == null) {
        try {
            console.log("Attempting to fetch settings")
            const response = await fetch(settingsUrl, {
                method: 'GET',
                headers: {
                    'Accept' : 'application/json'
                },
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status} - ${response.statusText}`);
            }

            const data = await response.json();

            persistentSettings = data["settings"];
            return data["settings"];
        } catch (err) {
            console.error('Failed to fetch settings JSON:', err);
            throw err;
        }
    } else {
        console.log("Using cached settings")
        return persistentSettings;
    }

}

document.addEventListener('fragmentloaded', e => {
    const page = e.detail.page;          // e.g. "settings"
    const registry = window.pageInits || {};

    console.log(registry)

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

window.pageIntervals = window.pageIntervals || {};
window.pageIntervals.temporary = window.pageIntervals.temporary || [];
window.pageIntervals.persistent = window.pageIntervals.persistent || {};
window.pageInits = window.pageInits || {};