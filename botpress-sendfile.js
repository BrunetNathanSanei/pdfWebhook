const url_get_file_list = 'http://37.187.39.26:5000/get_file_list' // URL to send the request to

let file_url = event.payload.fileUrl
// const file_url = event.payload.fileUrl // Get the file from the event payload

if (!file_url) {
  const file_url = event.payload['items'][0]['payload']['fileUrl']
}

const formData = new FormData() // Create a new FormData object
formData.append('file_url', file_url) // Append the file to the FormData

const response = await axios.post(url_get_file_list, formData) // Make a POST request with the FormData

const fileList = response.data
console.log(fileList)
//workflow.extractedText = console.log(file_url)

const textList = workflow.extractedText
const url_get_text = 'http://37.187.39.26:5000/get_text'

for (const file of fileList) {
  const formData = new FormData()
  formData.append('file_path', file)
  const text = await axios.post(url_get_text, formData)
  textList.push(text.data)
}

await axios.get('http://37.187.39.26:5000/remove_file')

workflow.extractedText = textList



async function testDeleteFile() {
  const url = 'http://37.187.39.26:5000/remove_file'
  const response = await fetch(url)
  console.log(response.status)
}
/*
const fileList = await testGetFilesList(file_url);
const textList = [];

for (const file of fileList) {
  const text = await testGetText(file);
  textList.push(text);
}*/
