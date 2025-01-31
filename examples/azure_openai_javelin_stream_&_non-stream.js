import axios from 'axios';
import { Stream } from 'openai/streaming.mjs';

const javelinApiKey = ""; // javelin api key here
const llmApiKey = ""; // llm api key

const javelinBaseUrl = 'https://api-dev.javelin.live/v1/query';

async function getCompletion() {
  try {
    const routeName = 'AzureOpenAIRoute';
    const url = "https://api-dev.javelin.live/v1/query/AzureOpenAIRoute";

    const response = await axios.post(
      url,
      {
        messages: [
          { role: 'system', content: 'Hello, you are a helpful scientific assistant.' },
          { role: 'user', content: 'What is the chemical composition of sugar?' },
        ],
        model: 'gpt-3.5-turbo',
      },
      {
        headers: {
          'x-api-key': javelinApiKey,
          'api-key': llmApiKey,
        },
      }
    );
    console.log(response.data.choices[0].message.content);
  } catch (error) {
    if (error.response) {
      console.error('Error status:', error.response.status);
      console.error('Error data:', error.response.data);
    } else {
      console.error('Error message:', error.message);
    }
  }
}


// Function to stream responses from the API
async function streamCompletion() {
  try {
    const url = "https://api-dev.javelin.live/v1/query/AzureOpenAIRoute";

    const response = await axios({
      method: 'post',
      url: url,
      data: {
        messages: [
          { role: 'system', content: 'Hello, you are a helpful scientific assistant.' },
          { role: 'user', content: 'What is the chemical composition of sugar?' },
        ],
        model: 'gpt-3.5-turbo',
      },
      headers: {
        'x-api-key': javelinApiKey,
        'api-key': llmApiKey,
      },
      responseType: 'stream', // Enable streaming response
    });

    response.data.on('data', (chunk) => {
      const decodedChunk = chunk.toString(); // Decode the chunk
      console.log('Chunk:', decodedChunk);
    });

    response.data.on('end', () => {
      console.log('Streaming complete.');
    });

    response.data.on('error', (err) => {
      console.error('Stream error:', err.message);
    });

  } catch (error) {
    if (error.response) {
      console.error('Error status:', error.response.status);
      console.error('Error data:', error.response.data);
    } else {
      console.error('Error message:', error.message);
    }
  }
}

// streamCompletion();


// Execute the functions
getCompletion();  // To get a single completion
streamCompletion();  // To stream completions
