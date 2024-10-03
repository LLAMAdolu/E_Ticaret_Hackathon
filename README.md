# LLAMAdolu E-Commerce Hackathon Project

## Project Overview
LLAMAdolu is an innovative web application designed to enhance the e-commerce experience for sellers of regional products. Our project combines state-of-the-art text processing with image enhancement technologies to help sellers bring their local products to a global market. Through the use of large language models and image processing pipelines, LLAMAdolu simplifies the process of improving product descriptions and images, ensuring that regional products stand out in online marketplaces.

## Team

1) Team Name : LLAMAdolu
2) Members:
   - Emirhan Soylu
   - Zahid Esad Baltacı
   - Yusuf Batur
   - Advisor: Ali Nizam

## Project Purpose 

The main goals of LLAMAdolu are:
- Ease of Use: Help local product sellers easily manage and enhance their product listings.
- Global Exposure: Facilitate the introduction of regional products to the global market.
- Improved Searchability: Make it easier for customers to search and discover local products online.

## Key Features

### Text-Based Features Using Large Language Models

- Product Description Generation: Automatically generate product descriptions based on images and metadata.
- Text Enhancement: Improve and optimize existing product descriptions using regional language and vocabulary.
- Globalization: Translating local expressions found in products into a language that everyone can understand for globalization.

### Image Processing Features

- Object Masking: The platform uses an automatic object masking technique to isolate the product from its background. By leveraging the rembg library, LLAMAdolu creates a detailed mask of the object by removing the background, enabling further processing like background replacement or refinement.
- Reverse Masking: After obtaining the object mask, LLAMAdolu can reverse the mask, converting transparent areas to opaque and vice versa. This reversed mask helps in creating dynamic visual effects for background or object adjustments.
- Mask Blurring: To provide a smooth transition between the object and the background, LLAMAdolu blurs the edges of the object mask. Using the Stable Diffusion model, the mask is softened to create a seamless integration between the product and any new background.
- Inpainting with Stable Diffusion: LLAMAdolu utilizes the stabilityai/stable-diffusion-xl-refiner-1.0 model for inpainting, which allows the system to replace or improve the background of product images based on specific prompts. This feature ensures that the product stands out in a visually appealing manner with a new custom background suited to the seller's preferences.
- Image Upscaling: The platform uses Real-ESRGAN to upscale images while maintaining or enhancing their quality. This is especially useful for improving low-resolution images of products, making them more suitable for e-commerce platforms.
- Resizing to Original Dimensions: Once the image has been enhanced and upscaled, LLAMAdolu can resize it to match the original product image dimensions. This ensures that the enhanced images fit seamlessly into any existing platform or e-commerce site, preserving their visual integrity.

## Search and Discovery

- Localized Search: Enable customers to search for products based on regional keywords.
- Similar Product Search: Find products similar in taste, style, or category using AI-based recommendations.

## Technologies Used

- Streamlit: Framework for building the web interface of the application.
- LLama 3.2 3B(Large Language Model): For text generation and improvement.
- Real-ESRGAN: For enhancing product images.
- Stable Diffusion: For enhancing product images
- PyTorch, torchvision, Pillow: Libraries for machine learning and image processing.
- Bootstrap: CSS framework for responsive and modern UI design.

## Innovative Functions

- Text Processing with Localized Data: Enhance product descriptions using a dictionary enriched with local words and phrases.
- Image Processing Pipeline: Automatically suggest and apply background improvements to product images, giving sellers multiple options to choose from.
- User-Centric Design: Provide both buyers and sellers with a seamless experience in managing products and browsing listings.

## Project Workflow

1) Image Upload: Sellers upload product images to the platform.
2) Image Enhancement: The platform uses Real-ESRGAN to enhance image quality and suggests different background images.
3) Text Generation: The LLama model generates product descriptions based on images and metadata.
4) Final Listing: The seller selects the best image and description, and the product is published for buyers to see.

## Future Goals

We plan to expand LLAMAdolu by:

- Further Optimizing Localized Language Support: Train models with more regional data to enhance the cultural richness of product descriptions.
- Expand Image Processing Capabilities: Allow more complex edits and suggestions for product images, such as automatic cropping and scaling for different platforms.
- Scalability: Improve the system to support more sellers and buyers by optimizing backend services for faster processing.
- Improvement speed of model
