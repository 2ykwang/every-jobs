function highlight(text) {
  const tags = document.getElementsByTagName("p");
  console.log(tags);
  for (const inputText of tags) {
    let innerHTML = inputText.innerHTML;
    const index = innerHTML.toLowerCase().indexOf(text.toLowerCase());
    if (index >= 0) {
      innerHTML =
        innerHTML.substring(0, index) +
        "<span class='nes-text is-success'>" +
        innerHTML.substring(index, index + text.length) +
        "</span>" +
        innerHTML.substring(index + text.length);
      inputText.innerHTML = innerHTML;
    }
  }
}
