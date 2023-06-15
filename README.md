# LabelScreenshotOCR
Batch-processing of PNG screenshots to output a JSON file in the same format as [LabelMe](https://github.com/wkentaro/labelme/) project does. It scans the image, label all the places with text, and insert recognized text in the 'description' field of JSON.

How to use

1. Install all the dependencies (OpenCV, EasyORC)
2. Change the language code to whatever you're about to scan
3. Put your screenshots in the 'sample' subfolder from where you're running this script
4. Shazam!
5. All the JSONs are in the same folder with the same name.
