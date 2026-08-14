const LOADER = document.getElementById("loader-wrapper")
const POPUP = document.getElementById("popup")

function handleBadRequest() {
    alert("Invalid request. Please try again.");
}

function handleUnauthorized(){
    alert("User not logged in or session expired.");
    window.location.replace("/login");
}

function handleInternalServerError() {
    alert("Internal server error occurred.");
}

function parseDuration(duration) {
    const units = ["second", "minute", "hour", "day"];

    return duration
        .split(':')
        .reverse()
        .map((val, index) => {
          const num = parseInt(String(val), 10) || 0;
          if (num === 0)
              return ""

          const unit = units[index] || "unknown";
          const suffix = (num === 1 || unit === "unknown") ? "" : "s";

          return `${num} ${unit}${suffix}`;
        })
        .reverse()
        .join(' ');
}

document.querySelectorAll(".save-btn").forEach(button => {
    button.addEventListener("click", async (event) => {
        event.preventDefault();
        event.stopPropagation();

        const channelId = button.dataset.channel_id;
        const playlistId = button.dataset.playlist_id;

        LOADER.style.display = "flex";
        button.textContent = "Saving...";

        try {
            /// Check if the channel exists
            let channel_exists = false;
            let response = await fetch(`/api/channels/${channelId}`);
            if (response.status === 401)
                return handleUnauthorized();
            channel_exists = response.ok;

            /// If channel does not exist, try to save it
            if (!channel_exists) {
                response = await fetch("/api/channels", {
                    method: "POST",
                    headers: {"Content-Type": "application/json"},
                    body: JSON.stringify({channel_id: channelId})
                });

                if (!response.ok) {
                    if (response.status === 400)
                        return handleBadRequest();
                    if (response.status === 401)
                        return handleUnauthorized();
                    if (response.status === 409)
                        console.log("Channel already exists.");
                    if (response.status === 500)
                        return handleInternalServerError();
                }
            }

            /// Try to save the playlist
            response = await fetch("/api/playlists", {
                method: "POST",
                headers: {"Content-Type": "application/json"},
                body: JSON.stringify({channel_id: channelId, playlist_id: playlistId})
            });

            if (!response.ok) {
                if (response.status === 400)
                    return handleBadRequest();
                if (response.status === 401)
                    return handleUnauthorized();
                if (response.status === 409) {
                    alert("This playlist is already saved.")
                    button.textContent = "Already saved!";
                    button.disabled = true;
                    return;
                }
                if (response.status === 500)
                    return handleInternalServerError();
            }

            /// Try to save the playlist's videos
            response = await fetch("/api/videos", {
                method: "POST",
                headers: {"Content-Type": "application/json"},
                body: JSON.stringify({playlist_id: playlistId})
            });

            if (!response.ok) {
                if (response.status === 400)
                    return handleBadRequest();
                if (response.status === 401)
                    return handleUnauthorized();
                if (response.status === 500)
                    return handleInternalServerError();
            }

            button.textContent = "Saved!";
            button.disabled = true;
        }
        catch (error) {
            console.error("An error occurred: ", error);
            button.textContent = "Error";
        }
        finally {
            LOADER.style.display = "none";
        }
    });
});

document.querySelectorAll(".delete-btn").forEach(button => {
    button.addEventListener("click", async (event) => {
        event.preventDefault();
        event.stopPropagation();

        const confirmed = confirm("Are you sure to delete this playlist?");
        if (!confirmed) return;

        const playlistId = button.dataset.playlist_id;

        LOADER.style.display = "flex";
        button.textContent = "Deleting...";

        try {
            const response = await fetch(`/api/playlists/${playlistId}`, { method: "DELETE" });

            if (!response.ok) {
                if (response.status === 401)
                    return handleUnauthorized();
                if (response.status === 404) {
                    alert("This playlist was not found.");
                    button.textContent = "Already deleted!";
                    button.disabled = true;
                    return;
                }
                if (response.status === 500)
                    return handleInternalServerError();
            }

            button.textContent = "Deleted!";
            button.disabled = true;
        }
        catch (error) {
            console.error("An error occurred: ", error);
            button.textContent = "Error";
        }
        finally {
            LOADER.style.display = "none";
        }
    });
});

document.querySelectorAll(".watch-btn").forEach(button => {
    button.addEventListener("click", async (event) => {
        event.preventDefault();
        event.stopPropagation();

        const videoId = button.dataset.video_id;

        LOADER.style.display = "flex";
        button.textContent = "Please wait...";

        try {
            const is_watched = button.classList.contains("watched");

            const response = await fetch(`/api/videos/${videoId}`, {
                method: "PATCH",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ watched: !is_watched })
            })

            if (!response.ok) {
                if (response.status === 400)
                    return handleBadRequest();
                if (response.status === 401)
                    return handleUnauthorized();
                if (response.status === 404) {
                    alert("Please save the playlist first!");
                    button.textContent = "Not watched";
                    return;
                }
                if (response.status === 500)
                    return handleInternalServerError();
            }

            const data = await response.json();

            if (data.watched) {
                button.textContent = "Watched";
                button.classList.add("watched");
            }
            else {
                button.textContent = "Not watched";
                button.classList.remove("watched");
            }
        }
        catch (error) {
            console.error("An error occurred: ", error);
            button.textContent = "Error";
        }
        finally {
            LOADER.style.display = "none";
        }
    });
});

document.querySelector(".watch-all-btn")?.addEventListener("click", async (event) => {
    event.preventDefault();
    event.stopPropagation();

    const confirmed = confirm("Are you sure to watch/unwatch the entire playlist?");
    if (!confirmed) return;

    const button = event.currentTarget;
    const playlistId = button.dataset.playlist_id

    LOADER.style.display = "flex";
    button.textContent = "Please wait..."

    try {
        const is_watched = button.classList.contains("watched");

        const response = await fetch(`/api/videos`, {
            method: "PATCH",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                playlist_id: playlistId,
                watched: !is_watched
            })
        });

        if (!response.ok) {
            if (response.status === 400)
                return handleBadRequest();
            if (response.status === 401)
                return handleUnauthorized();
            if (response.status === 404) {
                alert("Please save the playlist first!");
                button.textContent = "Watch all";
                return;
            }
            if (response.status === 500)
                return handleInternalServerError();
        }

        const data = await response.json();

        /// Update the 'watch all' button and all the 'watch' buttons
        if (data.watched) {
            button.classList.add("watched");
            button.textContent = "Unwatch all";
            document.querySelectorAll(".watch-btn").forEach(b => {
                b.classList.add("watched");
                b.textContent = "Watched";
            });
        }
        else {
            button.classList.remove("watched");
            button.textContent = "Watch all";
            document.querySelectorAll(".watch-btn").forEach(b => {
                b.classList.remove("watched");
                b.textContent = "Not watched";
            });
        }
    }
    catch (error) {
        console.error("An error occurred: ", error);
        button.textContent = "Error";
    }
    finally {
        LOADER.style.display = "none";
    }
});

document.querySelector(".refresh-btn")?.addEventListener("click", async (event) => {
    event.preventDefault();
    event.stopPropagation();

    const button = event.currentTarget;
    const playlistId = button.dataset.playlist_id;

    LOADER.style.display = "flex";
    button.disabled = true;
    button.textContent = "Refreshing...";

    try {
        let response = await fetch(`/api/playlists/${playlistId}`, { method: "PUT" });

        if (!response.ok) {
            if (response.status === 401)
                return handleUnauthorized();
            if (response.status === 404) {
                alert("This playlist is not saved.")
                button.textContent = "Refresh";
                return;
            }
            if (response.status === 500)
                return handleInternalServerError();
        }

        response = await fetch("/api/videos", {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ playlist_ids: [playlistId] })
        });

        if (!response.ok) {
            if (response.status === 401)
                return handleUnauthorized();
            if (response.status === 500)
                return handleInternalServerError();
        }

        button.textContent = "Refreshed!";
    }
    catch (error) {
        console.error("An error occurred: ", error);
        button.textContent = "Error";
    }
    finally {
        LOADER.style.display = "none";
        button.disabled = false;
    }
});

document.querySelector(".refresh-all-btn")?.addEventListener("click", async (event) => {
    event.preventDefault();
    event.stopPropagation();

    const button = event.currentTarget;
    const playlistIds = button.dataset.playlist_ids.split(",").filter(id => id)
    const total = playlistIds.length;

    if (total < 1)
        return;

    LOADER.style.display = "flex";
    button.disabled = true
    button.textContent = "Refreshing..."

    try {
        /// Refresh all playlists metadata at once
        let response = await fetch("/api/playlists", { method: "PUT" });
        if (!response.ok) {
            if (response.status === 401)
                return handleUnauthorized();
            if (response.status === 500) {
                button.textContent = "Refresh all";
                return handleInternalServerError();
            }
        }

        /// Refresh videos
        response = await fetch("/api/videos", {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ playlist_ids: playlistIds })
        });

        if (!response.ok) {
            if (response.status === 400)
                return handleBadRequest();
            if (response.status === 401)
                return handleUnauthorized();
            if (response.status === 500) {
                button.textContent = "Refresh all";
                return handleInternalServerError();
            }
        }

        button.textContent = "Refreshed!";
    }
    catch (error) {
        console.error("An error occurred: ", error);
        button.textContent = "Error";
    }
    finally {
        LOADER.style.display = "none";
        button.disabled = false;
    }
});

document.getElementById("closePopup")?.addEventListener("click", () => {
    POPUP.classList.remove("visible");
});

document.querySelector(".playlist-info-btn")?.addEventListener("click", (event) => {
    event.preventDefault();
    event.stopPropagation();

    const playlist = JSON.parse(document.getElementById("playlist-info").textContent);
    const plural = () => playlist["count"] === 1 ? "" : "s";

    document.getElementById("title").textContent = playlist["title"];
    document.getElementById("description").textContent = playlist["description"];
    document.getElementById("details").textContent =
        `Created: ${playlist["created"]} •
        ${playlist["count"]} video${plural()} •
        ${playlist["channel_name"]}`;

    POPUP.classList.add("visible");
});

document.querySelectorAll(".video-info-btn").forEach(button => {
    button.addEventListener("click", (event) => {
        event.preventDefault();
        event.stopPropagation();

        const video = JSON.parse(document.getElementById(`video-info-${button.dataset.video_id}`).textContent);

        document.getElementById("title").textContent = video["title"];
        document.getElementById("description").textContent = video["description"];
        document.getElementById("details").textContent =
            `${parseDuration(video["duration"])} •
            ${video["published"]} •
            ${video["channel_name"]}`;

        POPUP.classList.add("visible");
    });
});

document.querySelectorAll(".youtube-btn").forEach(button => {
    button.addEventListener("click", (event) => {
        event.preventDefault();
        event.stopPropagation();

        const type = button.dataset.type;
        const id = button.dataset.id;

        const confirmed = confirm(`Open this ${type} on YouTube?`);
        if (!confirmed)
            return;

        let url = "";
        if (type === "playlist") {
            url = `https://youtube.com/playlist?list=${id}`;
        }
        else if (type === "channel") {
            url = `https://youtube.com/channel/${id}`;
        }

        if (url) {
            // noinspection SpellCheckingInspection
            window.open(url, "_blank", "noopener, noreferrer");
        }
    });
});

document.querySelector(".delete-account-btn").addEventListener("click", () => {
    const confirmed = confirm("All your data will be permanently deleted. Are you sure?");
    if (!confirmed) return;

    document.getElementById("delete-account-button").style.display = "none"
    document.getElementById("delete-account-modal").style.display = "block";

    window.location.href = "/profile#delete-account-modal";
});

document.querySelector(".confirm-delete-btn").addEventListener("click", async (event) => {
    const userId = event.currentTarget.dataset.user_id;
    const passwordInput = document.getElementById("confirm-password")
    const password = passwordInput.value;

    try {
        if (!password) {
            return;
        }

        LOADER.style.display = "flex";

        const response = await fetch(`/api/users/${userId}`, {
            method: "DELETE",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({password: password})
        });

        if (!response.ok) {
            if (response.status === 400)
                return handleBadRequest();
            if (response.status === 401)
                return handleUnauthorized();
            if (response.status === 403) {
                alert("You don't have permissions to perform this action.");
                window.location.reload();
                return;
            }
            if (response.status === 404) {
                alert("The user was not found.");
                window.location.reload();
                return;
            }
            if (response.status === 422) {
                alert("The password is incorrect.");
                passwordInput.value = "";
                return;
            }
            if (response.status === 500)
                return handleInternalServerError();
        }

        window.location.replace("/login");
    }
    catch (error) {
        console.error("An error occurred: ", error);
    }
    finally {
        LOADER.style.display = "none";
    }
});

///// vvv TO-DO vvv /////

document.querySelectorAll(".preference-form select").forEach(select => {
    select.addEventListener("change", () => {
        const form = select.closest("form");

        LOADER.style.display = "flex";
        const body = new FormData(form)
        select.disabled = true;

        fetch("/set_preference", { method: "POST", body: body })
        .then(response => response.json())
        .then(data => {
            select.disabled = false;
            if (data.status === "success") {
                window.location.reload()
            }
            else if (data.status === "error") {
                console.error("Something went wrong.")
            }
        })
        .catch(err => {
            console.error(err);
            window.location.reload();
        })
        .finally(() => {
            LOADER.style.display = "none";
        })
    })
})

document.querySelectorAll(".preference-toggle input[type='checkbox']").forEach(checkbox => {
    checkbox.addEventListener("change", () => {
        const body = new FormData();
        body.append(checkbox.name, checkbox.checked ? "1" : "0");

        LOADER.style.display = "flex";
        checkbox.disabled = true;

        fetch("/set_preference", { method: "POST", body: body })
        .then(response => response.json())
        .then(data => {
            checkbox.disabled = false;
            if (data.status === "success") {
                window.location.reload()
            }
            else if (data.status === "error") {
                console.error("Something went wrong.")
            }
        })
        .catch(err => {
            console.error(err);
            window.location.reload();
        })
        .finally(() => {
            LOADER.style.display = "none";
        })
    })
})

/// SHOW LOADER WHEN SUBMITTING HTML FORMS AND CLICKING BUTTONS
document.addEventListener("DOMContentLoaded", () => {
    const forms = document.querySelectorAll(
        "#loginForm, #registerForm, #searchForm, #profileForm, #changePasswordForm"
    );

    const buttons = document.querySelectorAll(
        ".confirm-delete-btn"
    );

    forms.forEach(form => {
        form.addEventListener("submit", () => {
            LOADER.style.display = "flex";
        });
    });

    buttons.forEach(button => {
        button.addEventListener("click", () => {
            LOADER.style.display = "flex";
        });
    });
});

/// HIDE LOADER WHEN USING BACK BUTTON
window.addEventListener("pageshow", event => {
    if (event.persisted) {
        LOADER.style.display = "none";
    }
});

/// FOR APPLE IOS SAFARI STANDALONE APP
document.querySelectorAll("a").forEach(a => {
    a.addEventListener("click", e => {
        LOADER.style.display = "flex";
        // noinspection JSUnresolvedReference
        if (window.navigator.standalone && a.hostname === location.hostname) {
            e.preventDefault();
            window.location.href = a.href;
        }
    });
});