const captureButton = document.getElementById('capture');
const output = document.getElementById('output');

captureButton.addEventListener('click', async () => {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  output.textContent = JSON.stringify(
    {
      title: tab?.title ?? null,
      url: tab?.url ?? null,
    },
    null,
    2,
  );
});
