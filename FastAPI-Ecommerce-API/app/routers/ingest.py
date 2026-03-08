"""
Script to generate product reviews from actual PostgreSQL products and ingest into ChromaDB RAG.
"""
import os
import sys
import json
import random
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import psycopg2
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database configuration
DB_CONFIG = {
    "host": os.getenv("ECOMMERCE_DB_HOST", "localhost"),
    "port": int(os.getenv("ECOMMERCE_DB_PORT", "5433")),
    "database": os.getenv("ECOMMERCE_DB_NAME", "ecommerce_db"),
    "user": os.getenv("ECOMMERCE_DB_USER", "ecommerce_user"),
    "password": os.getenv("ECOMMERCE_DB_PASSWORD", "ecommerce_pass")
}

# Review templates for different sentiment levels
POSITIVE_TEMPLATES = [
    "Absolutely love this {product}! The quality from {brand} is exceptional. {specific}",
    "Best {category} purchase I've made. {brand} never disappoints. {specific}",
    "Five stars! This {product} exceeded my expectations. {specific}",
    "Highly recommend this {brand} {product}. {specific} Great value for the price!",
    "Outstanding quality! The {product} works exactly as described. {specific}",
    "Perfect {category} item! {brand} has done it again. {specific}",
    "So happy with this purchase! The {product} is amazing. {specific}",
    "This {brand} {product} is a game changer. {specific} Would buy again!",
    "Excellent product! {specific} The {brand} quality really shows.",
    "Can't believe how good this {product} is! {specific} Totally worth it.",
]

NEUTRAL_TEMPLATES = [
    "Decent {product} from {brand}. {specific} Gets the job done.",
    "Average {category} item. {specific} Nothing spectacular but works fine.",
    "The {product} is okay. {specific} Might look for alternatives next time.",
    "Fair quality from {brand}. {specific} Expected a bit more for the price.",
    "It's alright. The {product} {specific} Not bad, not great.",
    "Standard {brand} {product}. {specific} Does what it's supposed to do.",
    "Mediocre experience with this {category} item. {specific}",
    "The {product} meets basic expectations. {specific} Could be better.",
]

NEGATIVE_TEMPLATES = [
    "Disappointed with this {product}. {specific} Expected better from {brand}.",
    "Not impressed with the {category} item. {specific} Wouldn't recommend.",
    "Quality issues with this {brand} {product}. {specific}",
    "Returned this {product}. {specific} Not worth the money.",
    "Below average {category} item from {brand}. {specific}",
]

# Specific comments based on product categories
SPECIFIC_COMMENTS = {
    "electronics": [
        "Battery life is impressive.",
        "Setup was super easy.",
        "The Bluetooth connection is stable.",
        "Works seamlessly with my devices.",
        "Build quality feels premium.",
        "The buttons are responsive.",
        "Display is bright and clear.",
        "Charges quickly.",
        "Compact and portable design.",
        "The app integration works well.",
    ],
    "skincare": [
        "My skin feels so soft after using it.",
        "No irritation at all.",
        "Absorbs quickly without residue.",
        "Nice subtle fragrance.",
        "Keeps my skin hydrated all day.",
        "Noticed improvement within a week.",
        "Perfect for sensitive skin.",
        "A little goes a long way.",
        "Love the natural ingredients.",
        "Great for daily use.",
    ],
    "home": [
        "Fits perfectly in my space.",
        "Easy to assemble.",
        "Looks exactly like the pictures.",
        "Sturdy construction.",
        "Great addition to my home.",
        "Color matches well with my decor.",
        "Comfortable and practical.",
        "The material is high quality.",
        "Very functional design.",
        "Worth every penny for home use.",
    ],
    "garden": [
        "Makes gardening so much easier.",
        "Durable enough for outdoor use.",
        "Comfortable grip.",
        "Lightweight but sturdy.",
        "Perfect size for my garden.",
        "Holds up well in all weather.",
        "Professional quality tool.",
        "Great for both beginners and experts.",
        "Makes yard work enjoyable.",
        "Essential for any gardener.",
    ],
    "kitchen": [
        "Sharp blade right out of the box.",
        "Comfortable handle grip.",
        "Easy to clean.",
        "Professional quality for home use.",
        "Makes cooking preparation faster.",
        "Well balanced weight.",
        "Stays sharp after many uses.",
        "Safe and easy to store.",
        "Essential kitchen tool.",
        "Great for everyday cooking.",
    ],
    "health": [
        "Easy to swallow capsules.",
        "Noticed more energy within days.",
        "No unpleasant aftertaste.",
        "Good value for the quantity.",
        "Helps with my daily nutrition.",
        "Doctor recommended brand.",
        "Quality ingredients.",
        "Convenient daily serving.",
        "Supports my wellness routine.",
        "Effective supplement.",
    ],
    "fashion": [
        "Comfortable to wear all day.",
        "Stylish and practical.",
        "Quality materials used.",
        "Looks great with many outfits.",
        "Perfect fit as expected.",
        "Color is true to the photos.",
        "Well made stitching.",
        "Gets compliments all the time.",
        "Great everyday accessory.",
        "Classic design that lasts.",
    ],
    "default": [
        "Good product overall.",
        "Works as advertised.",
        "Happy with the purchase.",
        "Solid choice for the price.",
        "Would consider buying again.",
        "Meets my expectations.",
        "Nice quality product.",
        "Functional and reliable.",
        "Decent value.",
        "Satisfactory experience.",
    ]
}

REVIEWER_NAMES = [
    "Sarah M.", "John D.", "Emily R.", "Michael T.", "Jessica L.",
    "David K.", "Amanda P.", "Robert W.", "Jennifer H.", "Chris B.",
    "Lisa G.", "James S.", "Rachel F.", "Kevin C.", "Michelle N.",
    "Brian A.", "Nicole Y.", "Steven M.", "Ashley J.", "Daniel O.",
    "Samantha E.", "Andrew Z.", "Megan V.", "Ryan X.", "Stephanie Q.",
]


def get_product_category(title: str, brand: str) -> str:
    """Determine product category based on title and brand"""
    title_lower = title.lower()
    brand_lower = brand.lower()
    
    if any(word in title_lower for word in ['mouse', 'keyboard', 'usb', 'watch', 'lamp', 'clock']):
        return 'electronics'
    elif any(word in title_lower for word in ['cream', 'lipbalm', 'essences', 'skincare']):
        return 'skincare'
    elif any(word in title_lower for word in ['bedsheet', 'lamp', 'freshner', 'gift']):
        return 'home'
    elif any(word in title_lower for word in ['garden', 'gloves', 'watering', 'pruning', 'shears']):
        return 'garden'
    elif any(word in title_lower for word in ['knife', 'kitchen']):
        return 'kitchen'
    elif any(word in title_lower for word in ['vitamin', 'tablet', 'supplement']):
        return 'health'
    elif any(word in title_lower for word in ['watch', 'gift']):
        return 'fashion'
    else:
        return 'default'


def generate_review(product: dict, sentiment: str = "positive") -> dict:
    """Generate a single review for a product"""
    category = get_product_category(product['title'], product['brand'])
    
    if sentiment == "positive":
        template = random.choice(POSITIVE_TEMPLATES)
        rating = random.randint(4, 5)
    elif sentiment == "neutral":
        template = random.choice(NEUTRAL_TEMPLATES)
        rating = random.randint(3, 4)
    else:
        template = random.choice(NEGATIVE_TEMPLATES)
        rating = random.randint(1, 3)
    
    specific = random.choice(SPECIFIC_COMMENTS.get(category, SPECIFIC_COMMENTS['default']))
    
    review_text = template.format(
        product=product['title'],
        brand=product['brand'],
        category=category,
        specific=specific
    )
    
    # Random date in last 6 months
    days_ago = random.randint(1, 180)
    review_date = (datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%d")
    
    return {
        "product_id": product['id'],
        "product_title": product['title'],
        "product_brand": product['brand'],
        "product_price": float(product['price']),
        "reviewer_name": random.choice(REVIEWER_NAMES),
        "rating": rating,
        "review_text": review_text,
        "review_date": review_date,
        "verified_purchase": random.choice([True, True, True, False]),  # 75% verified
        "helpful_votes": random.randint(0, 50)
    }


def fetch_products_from_db() -> list:
    """Fetch all products from PostgreSQL"""
    print("📦 Connecting to PostgreSQL database...")
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, title, brand, price, description 
            FROM products 
            ORDER BY id
        """)
        
        columns = ['id', 'title', 'brand', 'price', 'description']
        products = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        cursor.close()
        conn.close()
        
        print(f"✅ Fetched {len(products)} products from database")
        return products
        
    except Exception as e:
        print(f"❌ Database error: {e}")
        raise


def generate_all_reviews(products: list, reviews_per_product: int = 10) -> list:
    """Generate reviews for all products"""
    print(f"\n📝 Generating {reviews_per_product} reviews per product...")
    
    all_reviews = []
    
    for product in products:
        # Distribution: 60% positive, 25% neutral, 15% negative
        sentiments = (
            ['positive'] * 6 + 
            ['neutral'] * 3 + 
            ['negative'] * 1
        )
        random.shuffle(sentiments)
        
        for i in range(reviews_per_product):
            sentiment = sentiments[i % len(sentiments)]
            review = generate_review(product, sentiment)
            all_reviews.append(review)
        
        print(f"  ✓ Generated {reviews_per_product} reviews for: {product['title']}")
    
    print(f"\n✅ Total reviews generated: {len(all_reviews)}")
    return all_reviews


def save_reviews_to_json(reviews: list, filepath: str):
    """Save reviews to JSON file"""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    
    with open(filepath, 'w') as f:
        json.dump(reviews, f, indent=2)
    
    print(f"💾 Saved reviews to: {filepath}")


def ingest_to_chroma(reviews: list):
    """Ingest reviews into ChromaDB vector store"""
    print("\n🔄 Ingesting reviews into ChromaDB...")
    
    from langchain_huggingface import HuggingFaceEmbeddings
    from langchain_chroma import Chroma
    from langchain_core.documents import Document
    
    # Initialize embeddings
    print("  Loading embedding model...")
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        model_kwargs={'device': 'cpu'}
    )
    
    # Prepare documents
    print("  Preparing documents...")
    documents = []
    for review in reviews:
        # Create rich document content
        content = f"""Product: {review['product_title']}
Brand: {review['product_brand']}
Price: ${review['product_price']}
Rating: {review['rating']}/5 stars
Review: {review['review_text']}
Reviewer: {review['reviewer_name']}
Date: {review['review_date']}
Verified Purchase: {'Yes' if review['verified_purchase'] else 'No'}"""
        
        doc = Document(
            page_content=content,
            metadata={
                "product_id": review['product_id'],
                "product_title": review['product_title'],
                "product_brand": review['product_brand'],
                "product_price": review['product_price'],
                "rating": review['rating'],
                "reviewer_name": review['reviewer_name'],
                "review_date": review['review_date'],
                "verified_purchase": review['verified_purchase'],
                "source": "product_reviews"
            }
        )
        documents.append(doc)
    
    # Create/update ChromaDB
    chroma_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "database",
        "chroma_db"
    )
    
    print(f"  Creating ChromaDB at: {chroma_path}")
    
    # Delete existing collection if it exists
    import shutil
    if os.path.exists(chroma_path):
        shutil.rmtree(chroma_path)
        print("  Removed existing ChromaDB")
    
    # Create new vector store
    vectorstore = Chroma.from_documents(
        documents=documents,
        embedding=embeddings,
        persist_directory=chroma_path,
        collection_name="product_reviews"
    )
    
    print(f"✅ Successfully ingested {len(documents)} reviews into ChromaDB")
    
    # Test retrieval
    print("\n🔍 Testing retrieval...")
    results = vectorstore.similarity_search("best quality products", k=3)
    print(f"  Sample search returned {len(results)} results")
    for i, doc in enumerate(results[:2]):
        print(f"  Result {i+1}: {doc.metadata.get('product_title', 'Unknown')}")
    
    return vectorstore


def main():
    print("=" * 60)
    print("🛒 Product Reviews RAG Ingestion Script")
    print("=" * 60)
    
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    json_path = os.path.join(base_dir, "database", "product_reviews.json")
    
    reviews = []
    
    # Check if reviews file exists
    if os.path.exists(json_path):
        print(f"📖 Loading existing reviews from: {json_path}")
        try:
            with open(json_path, 'r') as f:
                reviews = json.load(f)
            print(f"✅ Loaded {len(reviews)} reviews from file")
        except Exception as e:
            print(f"❌ Error loading reviews from file: {e}")
            reviews = []
    
    # If no reviews loaded, generate them
    if not reviews:
        print("📝 No existing reviews found. Generating new ones...")
        # Step 1: Fetch products
        try:
            products = fetch_products_from_db()
            # Step 2: Generate reviews (10 per product)
            reviews = generate_all_reviews(products, reviews_per_product=10)
            # Step 3: Save to JSON
            save_reviews_to_json(reviews, json_path)
        except Exception as e:
            print(f"❌ Failed to generate reviews: {e}")
            return

    # Step 4: Ingest to ChromaDB
    if reviews:
        ingest_to_chroma(reviews)
    
    print("\n" + "=" * 60)
    print("✅ All done! Reviews processed and ingested successfully.")
    print("=" * 60)


if __name__ == "__main__":
    main()
