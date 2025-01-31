// NOTE: this is for non streaming response.
import OpenAI from "openai";

const openai = new OpenAI({
  apiKey: "",  // add your api key
  baseURL: "https://api-dev.javelin.live/v1/query",
  defaultHeaders: {
    "x-api-key": "", // add here javelin api key
    "x-javelin-route": "OpenAIInspect",
  },
});

async function main() {
  try {
    const completion = await openai.chat.completions.create({
      messages: [{ role: "system", content: "You are a helpful assistant. Tell me a joke" }],
      model: "gpt-3.5-turbo",
    });

    const aiResponse = completion.choices[0]?.message?.content;
    console.log("AI Response:", aiResponse);
  } catch (error) {
    console.error("Error:", error);
  }
}

main();

// NOTE: this is for streaming response
import OpenAI from "openai";

const openai = new OpenAI({
  apiKey: "", // add your api key
  baseURL: "https://api-dev.javelin.live/v1/query",
  defaultHeaders: {
    "x-api-key": "",// add here javelin api key
    "x-javelin-route": "OpenAIInspect",
  },
});

async function main() {
  try {
    // Choose your query configuration
    const queryConfig = {
      messages: [{ role: "system", content: "You are a helpful assistant." }],
      model: "gpt-3.5-turbo",
      stream: true,
    };

    // Make the call and get the stream
    const stream = await openai.chat.completions.create(queryConfig);
    
    if (stream && stream.iterator) {
      console.log("Streamed AI Response:");

      // Now we can iterate over the stream
      for await (const chunk of stream.iterator()) {
        console.log("\nChunk Received:", chunk); // Print the raw chunk
        const part = chunk?.choices[0]?.delta?.content;
        if (part) {
          process.stdout.write(part); // Print the incremental response
        }
      }

      console.log("\nStreamed response completed.");
    } else {
      console.log("No stream returned.");
    }
  } catch (error) {
    console.error("Error:", error);
  }
}

main();
