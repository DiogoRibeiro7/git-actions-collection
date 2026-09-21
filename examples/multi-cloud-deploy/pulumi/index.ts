import * as aws from "@pulumi/aws";

const bucket = new aws.s3.Bucket("example");

export const bucketName = bucket.id;
