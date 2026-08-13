const functions = require("@google-cloud/functions-framework");
const { Storage } = require("@google-cloud/storage");

const storage = new Storage();

/**
 * Cloud Functions Gen2 - subscriber
 * Triggered by: Eventarc (Pub/Sub topic.messagePublished)
 * Action: Write processing result to output Cloud Storage bucket
 */
functions.cloudEvent("subscriber", async (cloudEvent) => {
  const message = cloudEvent.data.message;
  const data = JSON.parse(Buffer.from(message.data, "base64").toString());

  console.log(`Received message for: gs://${data.bucket}/${data.name}`);

  const outputBucket = process.env.OUTPUT_BUCKET;
  if (!outputBucket) {
    throw new Error("OUTPUT_BUCKET environment variable is not set");
  }

  const outputPath = `processed/${data.name}.json`;
  const content = JSON.stringify({
    ...data,
    processedAt: new Date().toISOString(),
    status: "success",
  });

  await storage.bucket(outputBucket).file(outputPath).save(content, {
    contentType: "application/json",
  });

  console.log(`Saved result to: gs://${outputBucket}/${outputPath}`);
});
