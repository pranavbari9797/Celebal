# Text Extraction from Images Using Azure Services

## Overview
This project extracts handwritten or printed text from images stored in an Azure Blob container, processes them using Azure Computer Vision, and uploads the result as JSON to an output container. The process is automated to trigger upon new image uploads and sends email notifications upon completion.

## Prerequisites
- Azure Subscription
- Azure Storage Account
- Azure Computer Vision Resource
- SendGrid Account for Email Notifications
