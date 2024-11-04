addEventListener('fetch', event => {
  event.respondWith(handleRequest(event.request))
})

addEventListener('scheduled', event => {
  event.waitUntil(handleScheduled())
})

async function handleRequest(request) {
  return await runScript();
}

async function handleScheduled() {
  await runScript();
}

async function runScript() {
  // URL of the CSV file
  const csvUrl = 'https://docs.google.com/spreadsheets/d/e/2PACX-1vQK4Tx46xhUHiBfe0G0qEmd2v7I5-2fBq55QYX2KgaFJA45l0wudK_-6au01cOEWckagx3g7ZqWkY9M/pub?gid=0&single=true&output=csv';

  // Fetch the CSV content
  const response = await fetch(csvUrl);
  const csvText = await response.text();

  // Parse CSV lines
  const lines = csvText.split('\n');
  const headers = lines[0].split(',');
  const websites = lines.slice(1);

  // Prepare output log
  let log = '';

  // Iterate through columns starting from the 5th column (index 4)
  for (let col = 4; col < headers.length; col++) {
    const fileUrl = headers[col].trim();

    if (fileUrl) {
      // Extract filename from URL, excluding the last slash
      const filename = fileUrl.substring(fileUrl.lastIndexOf('/') + 1);

      // Iterate through each row to find active tasks
      for (const row of websites) {
        const columns = row.split(',');
        const formUrl = columns[2].trim(); // Extract form URL (3rd column)
        const resultsUrl = columns[3].trim(); // Extract base URL from results column (4th column)
        const isActive = columns[col].trim();

        if (isActive === '1' && resultsUrl) {
          // Construct URL to check
          const constructedUrl = `${resultsUrl}${filename}`;

          try {
            // Check the HTTP status of the constructed URL
            const urlResponse = await fetch(constructedUrl, { method: 'HEAD' });

            if (urlResponse.status !== 200) {
              // If the status is not OK, send a POST request to the API
              const apiUrl = 'http://161.35.4.89:8327/upload';
              const payload = {
                url: formUrl, // Website form URL
                file_url: fileUrl, // Full file URL from header
              };

              const postResponse = await fetch(apiUrl, {
                method: 'POST',
                headers: {
                  'Content-Type': 'application/json',
                },
                body: JSON.stringify(payload),
              });

              // Extract the response body as JSON
              const responseBody = await postResponse.json();

              log += `Checked URL: ${constructedUrl} - Status: ${urlResponse.status} (Notification Sent)\n`;
              log += `POST Response: ${JSON.stringify(responseBody)}\n`;
            } else {
              log += `Checked URL: ${constructedUrl} - Status: ${urlResponse.status}\n`;
            }
          } catch (error) {
            log += `Error checking URL: ${constructedUrl} - ${error}\n`;
          }
        }
      }
    }
  }

  // Log output (for both direct request and scheduled runs)
  console.log(log);

  // Return log as response
  return new Response(log, { status: 200, headers: { 'content-type': 'text/plain' } });
}
