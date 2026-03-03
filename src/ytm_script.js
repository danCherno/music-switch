(function () {
  if (window.__musicSwitchInjected) return;
  window.__musicSwitchInjected = true;

  const video = document.querySelector('video');
  if (!video) return;

  window.__ytmState = {
    ended: false,
    currentTime: 0,
    duration: 0,
    title: '',
    artist: '',
    paused: true,
  };

  // Python resets ended — do NOT touch it in the interval.
  video.addEventListener('ended', () => {
    window.__ytmState.ended = true;
  });

  setInterval(() => {
    const titleEl = document.querySelector('.title.ytmusic-player-bar');
    const artistEl = document.querySelector('.byline.ytmusic-player-bar');
    Object.assign(window.__ytmState, {
      currentTime: video.currentTime,
      duration: video.duration,
      title: titleEl?.textContent?.trim() || '',
      artist: artistEl?.textContent?.trim() || '',
      paused: video.paused,
    });
  }, 500);
})();
