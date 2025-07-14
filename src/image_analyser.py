from PIL import Image
from openai import OpenAI
import pytesseract
import logging
import json
from json_repair import repair_json
from io import BytesIO

logger = logging.getLogger("image_analyser")

class ImageAnalyser:
    custom_config = r'--oem 3 --psm 6 -l eng'
    ai_question = """Extract menu items, descriptions and prices from this OCR text. Return only valid JSON in the following form:
    [{
        "name": "Grilled Chicken Caesar Salad",
        "keyword": "chicken caesar salad",
        "description": "null",
        "price": "$12.99"
    }]
    Keyword is the normalized keyword used to search for the image.
    Do not return anything else than valid JSON. Your response must start and end with brackets. Do not include duplicates.
    Ignore any text that is not a menu item, description or price. If you cannot extract any items, return an empty array.
    """

    def __init__(self, ai_model: str, api_key: str, base_url: str):
        self.ai_model = ai_model
        self.client = OpenAI(base_url=base_url, api_key=api_key)

    def analyse_image(self, image_input: str | bytes) -> list:
        """
        Analyzes an image to extract menu items using OCR and AI.
        :param image_input: Either a file path (str) or image bytes (bytes).
        :return: List of menu items as dictionaries.
        """
        logger.info("Reading image")
        text = self.ocr_image(image_input)
        logger.info(f"Extracted text: {text}")
        return self.parse_text_ai(text)

    def ocr_image(self, image_input: str | bytes) -> str:
        """
        Reads an image and extracts text using OCR.
        :param image_input: Either a file path (str) or image bytes (bytes).
        :return: Extracted text from the image.
        """
        if isinstance(image_input, str):
            image = Image.open(image_input)
        elif isinstance(image_input, bytes):
            image = Image.open(BytesIO(image_input))
        else:
            raise ValueError("image_input must be either a file path (str) or image bytes (bytes)")
        
        return pytesseract.image_to_string(image, config=self.custom_config)

    def parse_text_ai(self, text: str) -> list:
        """
        Calls the AI model to analyze the extracted text and return structured menu items.
        :param text: Extracted text from the image.
        :return: List of menu items as dictionaries.
        """
        logger.info("Calling AI model...")
        completion = self.client.chat.completions.create(
            extra_body={},
            model=self.ai_model,
            messages=[{
                "role": "user",
                "content": f"{self.ai_question}\n\n{text}"
            }])

        # Validate the response
        content = completion.choices[0].message.content
        print(f"AI response: {content}")  # Debugging output
        menu_items = []
        if content is not None:
            json_string = repair_json(content)
            try:
                result = json.loads(json_string)
                if isinstance(result, list):
                    logger.info("Valid JSON response received.")
                    menu_items = self.validate_menu_items(result)
                else:
                    logger.error(
                        f"Invalid JSON format received. {content}")
            except json.JSONDecodeError as e:
                logger.error(
                    f"JSON decoding error: {e} {content}")
        else:
            logger.error("AI response content is None.")
        return menu_items

    def validate_menu_items(self, items: list) -> list:
        """
        Validates menu items: Each entry must be a dict with 'name', 'description', and 'price'.
        Removes invalid entries and duplicates.
        """
        if not isinstance(items, list):
            return []
        valid = []
        seen = set()
        for item in items:
            if not isinstance(item, dict):
                continue
            name = item.get("name")
            price = item.get("price")
            # Name and price must be present
            if not name or not price:
                continue
            # Avoid duplicates
            key = (name.strip().lower(), price.strip())
            if key in seen:
                continue
            seen.add(key)
            # Description can be missing, set to "null" if so
            if "description" not in item:
                item["description"] = "null"
            valid.append({
                "name": name,
                "keyword": item.get("keyword", name),  # Use keyword if available, fallback to name
                "description": item["description"],
                "price": price
            })
        return valid
    


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="[%(levelname)s] [%(filename)s] %(message)s ",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    logger.info("Image Analyser module initialized.")
    # Example usage
    analyser = ImageAnalyser(
        ai_model="llama-3.1-8b-instant",
        api_key="API_KEY_HERE",
        base_url="https://api.groq.com/openai/v1"
    )
    menu_items = analyser.analyse_image("menu/test1.jpg")
    for item in menu_items:
        print(item)
