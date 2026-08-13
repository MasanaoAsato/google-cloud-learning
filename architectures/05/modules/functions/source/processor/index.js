const functions = require("@google-cloud/functions-framework");
const { PubSub } = require("@google-cloud/pubsub");

const pubsub = new PubSub();

/**
 * Cloud Functions Gen2 - processor
 * Triggered by: Eventarc (Cloud Storage object.finalized)
 * Action: Publish file metadata to Pub/Sub
 */
functions.cloudEvent("processor", async (cloudEvent) => {
  const file = cloudEvent.data;

  if (!file || !file.bucket) {
    throw new Error(`cloudEvent.data is missing or has no bucket field`);
  }

  console.log(`Processing file: gs://${file.bucket}/${file.name}`);

  const topicName = process.env.PUBSUB_TOPIC;
  if (!topicName) {
    throw new Error("PUBSUB_TOPIC environment variable is not set");
  }

  const message = {
    bucket: file.bucket,
    name: file.name,
    contentType: file.contentType,
    size: file.size,
    timeCreated: file.timeCreated,
  };

  await pubsub.topic(topicName).publishMessage({
    data: Buffer.from(JSON.stringify(message)),
    attributes: { source: "processor" },
  });

  console.log(`Published message for: gs://${file.bucket}/${file.name}`);
});
