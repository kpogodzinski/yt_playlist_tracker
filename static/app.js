document.querySelectorAll(".save-btn").forEach(button => {
    button.addEventListener("click", (event) => {
        event.preventDefault();
        event.stopPropagation();

        const playlistId = button.dataset.id

        button.textContent = "Saving...";

        fetch(`/save_playlist/${playlistId}`, { method: "POST" })
        .then(response => response.json())
        .then(data => {
            if (data.status === "success") {
                button.textContent = "Saved!";
                button.disabled = true;
            } else if (data.status === "exists") {
                button.textContent = "Already saved";
                button.disabled = true;
            }
        })
        .catch(err => console.error(err));
    });
});

document.querySelectorAll(".rm-btn").forEach(button => {
    button.addEventListener("click", (event) => {
        event.preventDefault();
        event.stopPropagation();

        const confirmed = confirm("Are you sure to remove this playlist?");
        if (!confirmed) return;

        const playlistId = button.dataset.id

        button.textContent = "Removing...";

        fetch(`/remove_playlist/${playlistId}`, { method: "POST" })
        .then(response => response.json())
        .then(data => {
            if (data.status === "success") {
                button.textContent = "Removed!";
                button.disabled = true;
            } else {
                button.textContent = "Error";
            }
        })
        .catch(err => console.error(err));
    });
});

document.querySelectorAll(".watch-btn").forEach(button => {
    button.addEventListener("click", (event) => {
        event.preventDefault();
        event.stopPropagation();

        const videoId = button.dataset.video

        button.textContent = "Please wait...";

        fetch(`/watch_video/${videoId}`, { method: "POST" })
        .then(response => response.json())
        .then(data => {
            if (data.status === "watched") {
                button.textContent = "Watched";
                button.classList.add("watched");
            } else if (data.status === "unwatched") {
                button.textContent = "Not watched"
                button.classList.remove("watched")
            } else if (data.status === "not saved") {
                button.textContent = "Save the playlist first!"
            } else {
                button.textContent = "Error"
            }

        })
        .catch(err => console.error(err));
    });
});

document.querySelectorAll(".watchall-btn").forEach(button => {
    button.addEventListener("click", () => {
        const playlistId = button.dataset.playlist

        button.textContent = "Please wait..."

        fetch(`/playlist/${playlistId}/watch_all`, {method: "POST"})
            .then(response => response.json())
            .then(data => {
                if (data.status === "watched") {
                    document.querySelectorAll(".watch-btn").forEach(button => {
                        button.classList.add("watched")
                        button.textContent = "Watched";
                    })
                    button.textContent = "Unwatch all"
                    button.classList.add("watched")
                } else if (data.status === "unwatched") {
                    document.querySelectorAll(".watch-btn").forEach(button => {
                        button.classList.remove("watched")
                        button.textContent = "Not watched";
                    })
                    button.textContent = "Watch all"
                    button.classList.remove("watched")
                } else if (data.status === "not saved") {
                    button.textContent = "Save the playlist first!"
                } else {
                    button.textContent = "Error"
                }
            })
    })
});

document.querySelectorAll(".fetch-btn").forEach(button => {
    button.addEventListener("click", () => {
        const playlistId = button.dataset.playlist

        button.disabled = true;
        button.textContent = "Refreshing..."

        fetch(`/fetch_playlist/${playlistId}`, {method: "POST"})
            .then(response => response.json())
            .then(data => {
                if (data.status === "success") {
                    button.textContent = "Refreshed!"
                    button.disabled = false
                }
            })
    })
});

document.querySelectorAll(".fetchall-btn").forEach(button => {
    button.addEventListener("click", async () => {
        const playlists = button.dataset.playlists.split(",").filter(id => id)
        const total = playlists.length
        if (total < 1) return

        button.disabled = true
        button.textContent = "Refreshing..."

        let done = 0
        for (const id of playlists) {
            const response = await fetch(`/fetch_playlist/${id}`, { method: "POST" })
            const data = await response.json()
            if (data.status === "success") {
                    done += 1
                    button.textContent = `Refreshing... (${done}/${total})`
                }
        }

        button.textContent = "Refreshed!"
        button.disabled = false
    })
});

document.querySelectorAll('a').forEach(a => {
  a.addEventListener('click', e => {
    if (window.navigator.standalone && a.hostname === location.hostname) {
      e.preventDefault();
      window.location.href = a.href;
    }
  });
});