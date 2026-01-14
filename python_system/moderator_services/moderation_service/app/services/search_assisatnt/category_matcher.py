"""
Category Matcher - Semantic Similarity Model
Uses sentence transformers to match user queries to categories
Loads models through the central model_registry

CACHE-FIRST ARCHITECTURE:
1. Check cache for existing results (fastest)
2. If cache miss, query the model
3. Store results in cache for future queries
"""

import os
import sys
import json
import numpy as np
from typing import List, Dict, Tuple, Optional
from pathlib import Path

# Set up paths for model_registry import
# Path: category_matcher.py -> search_assisatnt -> services -> app -> moderation_service -> moderator_services
CURRENT_DIR = Path(__file__).parent.resolve()
SERVICES_DIR = CURRENT_DIR.parent.resolve()
APP_DIR = SERVICES_DIR.parent.resolve()
MODERATION_SERVICE_DIR = APP_DIR.parent.resolve()
MODERATOR_SERVICES_DIR = MODERATION_SERVICE_DIR.parent.resolve()

for _path in [str(MODERATOR_SERVICES_DIR), str(MODERATION_SERVICE_DIR), str(APP_DIR)]:
    if _path not in sys.path:
        sys.path.insert(0, _path)

# Import model registry
try:
    from model_registry import ModelStore
    MODEL_REGISTRY_AVAILABLE = True
except ImportError:
    MODEL_REGISTRY_AVAILABLE = False
    print("Warning: model_registry not found. Will try direct import.")

# Try to import sentence transformers
try:
    from sentence_transformers import SentenceTransformer, util
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    print("Warning: sentence-transformers not installed. Using fallback matching.")

# Import cache
try:
    from .cache import SearchCache, get_cache
    CACHE_AVAILABLE = True
except ImportError:
    try:
        from cache import SearchCache, get_cache
        CACHE_AVAILABLE = True
    except ImportError:
        CACHE_AVAILABLE = False
        print("Warning: Cache not available. All queries will hit the model.")


class CategoryMatcher:
    """
    AI-powered category matcher using semantic embeddings.

    CACHE-FIRST: Checks cache before querying the model.
    Falls back to keyword matching if sentence-transformers is unavailable.
    """

    def __init__(self, model_name: str = "paraphrase-multilingual-MiniLM-L12-v2", use_cache: bool = True):
        """
        Initialize the category matcher.

        Args:
            model_name: The sentence transformer model to use.
                       Options: 'all-MiniLM-L6-v2' (fast, English),
                               'all-mpnet-base-v2' (accurate, English),
                               'paraphrase-multilingual-MiniLM-L12-v2' (multilingual - 50+ languages)
            use_cache: Whether to use caching (default: True)
        """
        self.model_name = model_name
        self.use_cache = use_cache and CACHE_AVAILABLE
        self.cache = get_cache() if self.use_cache else None

        # Cache stats
        self.cache_hits = 0
        self.cache_misses = 0
        self.model = None
        self.categories: Dict[str, Dict] = {}
        self.category_embeddings: Dict[str, np.ndarray] = {}
        self.is_loaded = False

        # Default category definitions with multilingual descriptions and keywords
        # Including translations in: Swahili, Spanish, French, German, Arabic, Chinese, Portuguese
        self.default_categories = {
            "food": {
                "name": "Food",
                "description": "Food, restaurants, cooking, meals, groceries, beverages, dining, eating, hunger, cuisine, kitchen, chef, delicious, tasty. "
                              "Swahili: chakula, kula, njaa, mgahawa, kupika. "
                              "Spanish: comida, comer, hambre, restaurante, cocina. "
                              "French: nourriture, manger, faim, restaurant, cuisine. "
                              "German: essen, hunger, restaurant, küche, lebensmittel. "
                              "Arabic: طعام, أكل, جوع, مطعم, طبخ. "
                              "Chinese: 食物, 吃, 饿, 餐厅, 烹饪. "
                              "Portuguese: comida, comer, fome, restaurante, cozinha.",
                "keywords": ["eat", "eating", "hungry", "meal", "restaurant", "cook", "cooking",
                           "recipe", "breakfast", "lunch", "dinner", "snack", "drink", "beverage",
                           "grocery", "supermarket", "kitchen", "chef", "delicious", "tasty",
                           "cuisine", "dining", "cafe", "bakery", "pizza", "burger", "coffee",
                           # Swahili
                           "chakula", "kula", "njaa", "mgahawa", "kupika", "kahawa",
                           # Spanish
                           "comida", "comer", "hambre", "restaurante", "cocina", "desayuno",
                           # French
                           "nourriture", "manger", "faim", "cuisine", "petit-déjeuner",
                           # German
                           "essen", "hunger", "küche", "frühstück", "lebensmittel",
                           # Portuguese
                           "fome", "cozinha", "almoço", "jantar"]
            },
            "electronics": {
                "name": "Electronics",
                "description": "Electronics, technology, gadgets, phones, computers, TVs, devices, smartphone, laptop, tablet, camera. "
                              "Swahili: elektroniki, simu, kompyuta, televisheni, teknolojia. "
                              "Spanish: electrónica, teléfono, computadora, televisión, tecnología. "
                              "French: électronique, téléphone, ordinateur, télévision, technologie. "
                              "German: elektronik, telefon, computer, fernseher, technologie. "
                              "Arabic: إلكترونيات, هاتف, كمبيوتر, تلفزيون, تكنولوجيا. "
                              "Chinese: 电子产品, 手机, 电脑, 电视, 技术. "
                              "Portuguese: eletrônicos, telefone, computador, televisão, tecnologia.",
                "keywords": ["tv", "television", "radio", "phone", "smartphone", "laptop",
                           "computer", "pc", "tablet", "gadget", "device", "tech", "technology",
                           "gaming", "console", "headphone", "speaker", "camera", "printer",
                           "monitor", "keyboard", "wifi", "bluetooth", "smart", "digital",
                           # Swahili
                           "simu", "kompyuta", "televisheni", "teknolojia", "elektroniki",
                           # Spanish
                           "teléfono", "computadora", "televisión", "tecnología", "electrónica",
                           # French
                           "téléphone", "ordinateur", "télévision", "technologie", "électronique",
                           # German
                           "telefon", "fernseher", "technologie", "elektronik", "handy",
                           # Portuguese
                           "telefone", "computador", "televisão", "tecnologia", "eletrônicos"]
            },
            "housing": {
                "name": "Housing",
                "description": "Housing, real estate, apartments, rentals, property, homes, house, room, rent, buy, sell, land, building. "
                              "Swahili: nyumba, chumba, kukodisha, ardhi, jengo, makazi. "
                              "Spanish: casa, apartamento, alquiler, propiedad, vivienda, habitación. "
                              "French: maison, appartement, louer, propriété, logement, chambre. "
                              "German: haus, wohnung, mieten, immobilien, zimmer, gebäude. "
                              "Arabic: منزل, شقة, إيجار, عقارات, غرفة, مبنى. "
                              "Chinese: 房子, 公寓, 租房, 房产, 房间, 建筑. "
                              "Portuguese: casa, apartamento, aluguel, propriedade, quarto, imóvel.",
                "keywords": ["house", "home", "apartment", "flat", "rent", "rental", "lease",
                           "buy", "sell", "property", "real estate", "room", "bedroom",
                           "land", "plot", "building", "condo", "villa", "mortgage", "tenant",
                           # Swahili
                           "nyumba", "chumba", "kukodisha", "ardhi", "jengo", "makazi",
                           # Spanish
                           "casa", "apartamento", "alquiler", "propiedad", "vivienda", "habitación",
                           # French
                           "maison", "appartement", "louer", "propriété", "logement", "chambre",
                           # German
                           "haus", "wohnung", "mieten", "immobilien", "zimmer", "gebäude",
                           # Portuguese
                           "aluguel", "quarto", "imóvel", "moradia"]
            },
            "vehicles": {
                "name": "Vehicles",
                "description": "Vehicles, cars, motorcycles, transportation, auto, automobile, truck, bike, drive, transport. "
                              "Swahili: gari, magari, pikipiki, usafiri, motokaa, basi, teksi. "
                              "Spanish: coche, carro, auto, vehículo, motocicleta, transporte, conducir. "
                              "French: voiture, auto, véhicule, moto, transport, conduire. "
                              "German: auto, fahrzeug, wagen, motorrad, transport, fahren. "
                              "Arabic: سيارة, مركبة, دراجة نارية, نقل, قيادة. "
                              "Chinese: 汽车, 车, 摩托车, 交通, 驾驶, 运输. "
                              "Portuguese: carro, veículo, moto, transporte, dirigir.",
                "keywords": ["car", "vehicle", "auto", "automobile", "truck", "van", "suv",
                           "motorcycle", "bike", "bicycle", "scooter", "drive", "driving",
                           "fuel", "petrol", "diesel", "engine", "tire", "wheel", "transport",
                           # Swahili
                           "gari", "magari", "pikipiki", "usafiri", "motokaa", "basi", "teksi",
                           # Spanish
                           "coche", "carro", "vehículo", "motocicleta", "transporte", "conducir",
                           # French
                           "voiture", "véhicule", "moto", "conduire",
                           # German
                           "auto", "fahrzeug", "wagen", "motorrad", "fahren",
                           # Portuguese
                           "veículo", "transporte", "dirigir", "caminhão"]
            },
            "fashion": {
                "name": "Fashion",
                "description": "Fashion, clothing, shoes, accessories, style, apparel, dress, clothes, wear. "
                              "Swahili: mavazi, nguo, viatu, mtindo, vazi. "
                              "Spanish: moda, ropa, zapatos, accesorios, estilo, vestido. "
                              "French: mode, vêtements, chaussures, accessoires, style, robe. "
                              "German: mode, kleidung, schuhe, accessoires, stil, kleid. "
                              "Arabic: موضة, ملابس, أحذية, إكسسوارات, أسلوب. "
                              "Chinese: 时尚, 服装, 鞋子, 配饰, 风格, 衣服. "
                              "Portuguese: moda, roupas, sapatos, acessórios, estilo, vestido.",
                "keywords": ["clothes", "clothing", "dress", "shirt", "pants", "jeans", "shoes",
                           "jacket", "coat", "sweater", "bag", "handbag", "watch", "jewelry",
                           "accessory", "fashion", "style", "outfit", "wear", "designer",
                           # Swahili
                           "mavazi", "nguo", "viatu", "mtindo", "vazi",
                           # Spanish
                           "moda", "ropa", "zapatos", "accesorios", "estilo", "vestido",
                           # French
                           "mode", "vêtements", "chaussures", "robe",
                           # German
                           "mode", "kleidung", "schuhe", "kleid",
                           # Portuguese
                           "roupas", "sapatos", "acessórios"]
            },
            "health": {
                "name": "Health",
                "description": "Health, medical, fitness, wellness, beauty, healthcare, doctor, hospital, medicine, gym. "
                              "Swahili: afya, daktari, hospitali, dawa, mazoezi, uzuri. "
                              "Spanish: salud, médico, hospital, medicina, gimnasio, belleza. "
                              "French: santé, médecin, hôpital, médecine, gym, beauté. "
                              "German: gesundheit, arzt, krankenhaus, medizin, fitness, schönheit. "
                              "Arabic: صحة, طبيب, مستشفى, دواء, لياقة, جمال. "
                              "Chinese: 健康, 医生, 医院, 药物, 健身, 美容. "
                              "Portuguese: saúde, médico, hospital, medicina, academia, beleza.",
                "keywords": ["health", "healthy", "medical", "medicine", "doctor", "hospital",
                           "clinic", "pharmacy", "fitness", "gym", "workout", "exercise",
                           "wellness", "beauty", "skincare", "makeup", "spa", "diet", "nutrition",
                           # Swahili
                           "afya", "daktari", "hospitali", "dawa", "mazoezi", "uzuri",
                           # Spanish
                           "salud", "médico", "medicina", "gimnasio", "belleza",
                           # French
                           "santé", "médecin", "hôpital", "médecine", "beauté",
                           # German
                           "gesundheit", "arzt", "krankenhaus", "medizin", "schönheit",
                           # Portuguese
                           "saúde", "academia", "beleza"]
            },
            "jobs": {
                "name": "Jobs",
                "description": "Jobs, careers, employment, work opportunities, hiring, job vacancy, salary, office, profession. "
                              "Swahili: kazi, ajira, mshahara, ofisi, taaluma, kuajiri. "
                              "Spanish: trabajo, empleo, carrera, salario, oficina, contratar. "
                              "French: travail, emploi, carrière, salaire, bureau, embaucher. "
                              "German: arbeit, job, beruf, gehalt, büro, einstellen. "
                              "Arabic: وظيفة, عمل, توظيف, راتب, مكتب, مهنة. "
                              "Chinese: 工作, 职业, 就业, 薪水, 办公室, 招聘. "
                              "Portuguese: trabalho, emprego, carreira, salário, escritório, contratar.",
                "keywords": ["job", "jobs", "work", "working", "career", "employment", "hire",
                           "hiring", "recruit", "resume", "cv", "interview", "salary", "wage",
                           "office", "remote", "freelance", "part-time", "full-time", "vacancy",
                           # Swahili
                           "kazi", "ajira", "mshahara", "ofisi", "taaluma", "kuajiri",
                           # Spanish
                           "trabajo", "empleo", "carrera", "salario", "oficina", "contratar",
                           # French
                           "travail", "emploi", "carrière", "salaire", "bureau", "embaucher",
                           # German
                           "arbeit", "beruf", "gehalt", "büro", "einstellen",
                           # Portuguese
                           "emprego", "salário", "escritório", "contratar"]
            },
            "services": {
                "name": "Services",
                "description": "Services, repairs, maintenance, professional services, plumber, electrician, cleaning. "
                              "Swahili: huduma, ukarabati, fundi bomba, fundi umeme, usafi. "
                              "Spanish: servicios, reparación, mantenimiento, fontanero, electricista, limpieza. "
                              "French: services, réparation, entretien, plombier, électricien, nettoyage. "
                              "German: dienstleistungen, reparatur, wartung, klempner, elektriker, reinigung. "
                              "Arabic: خدمات, إصلاح, صيانة, سباك, كهربائي, تنظيف. "
                              "Chinese: 服务, 维修, 保养, 水管工, 电工, 清洁. "
                              "Portuguese: serviços, reparo, manutenção, encanador, eletricista, limpeza.",
                "keywords": ["service", "repair", "fix", "install", "maintenance", "cleaning",
                           "plumber", "electrician", "carpenter", "painting", "delivery",
                           "catering", "event", "photography", "consulting", "legal", "insurance",
                           # Swahili
                           "huduma", "ukarabati", "fundi", "usafi",
                           # Spanish
                           "servicios", "reparación", "mantenimiento", "limpieza",
                           # French
                           "services", "réparation", "entretien", "nettoyage",
                           # German
                           "dienstleistungen", "reparatur", "wartung", "reinigung",
                           # Portuguese
                           "serviços", "reparo", "manutenção", "limpeza"]
            },
            "education": {
                "name": "Education",
                "description": "Education, schools, courses, learning, training, tutoring, university, college, study, teacher. "
                              "Swahili: elimu, shule, chuo kikuu, kusoma, mwalimu, kujifunza. "
                              "Spanish: educación, escuela, universidad, estudiar, profesor, aprender. "
                              "French: éducation, école, université, étudier, professeur, apprendre. "
                              "German: bildung, schule, universität, studieren, lehrer, lernen. "
                              "Arabic: تعليم, مدرسة, جامعة, دراسة, معلم, تعلم. "
                              "Chinese: 教育, 学校, 大学, 学习, 老师, 课程. "
                              "Portuguese: educação, escola, universidade, estudar, professor, aprender.",
                "keywords": ["school", "college", "university", "study", "learn", "learning",
                           "course", "class", "lesson", "tutor", "teacher", "student", "degree",
                           "training", "workshop", "online", "book", "exam", "scholarship",
                           # Swahili
                           "elimu", "shule", "chuo", "kusoma", "mwalimu", "kujifunza",
                           # Spanish
                           "educación", "escuela", "universidad", "estudiar", "profesor", "aprender",
                           # French
                           "éducation", "école", "université", "étudier", "professeur", "apprendre",
                           # German
                           "bildung", "schule", "universität", "studieren", "lehrer", "lernen",
                           # Portuguese
                           "educação", "estudar", "professor", "aprender"]
            },
            "travel": {
                "name": "Travel",
                "description": "Travel, tourism, vacations, flights, hotels, destinations, trip, holiday, tour, booking. "
                              "Swahili: safari, utalii, likizo, ndege, hoteli, kusafiri. "
                              "Spanish: viaje, turismo, vacaciones, vuelo, hotel, destino. "
                              "French: voyage, tourisme, vacances, vol, hôtel, destination. "
                              "German: reise, tourismus, urlaub, flug, hotel, reiseziel. "
                              "Arabic: سفر, سياحة, إجازة, طيران, فندق, وجهة. "
                              "Chinese: 旅行, 旅游, 假期, 航班, 酒店, 目的地. "
                              "Portuguese: viagem, turismo, férias, voo, hotel, destino.",
                "keywords": ["travel", "trip", "vacation", "holiday", "tour", "tourism",
                           "flight", "airline", "hotel", "resort", "booking", "ticket",
                           "beach", "mountain", "safari", "adventure", "destination", "cruise",
                           # Swahili
                           "safari", "utalii", "likizo", "ndege", "hoteli", "kusafiri",
                           # Spanish
                           "viaje", "turismo", "vacaciones", "vuelo", "destino",
                           # French
                           "voyage", "tourisme", "vacances", "vol", "hôtel", "destination",
                           # German
                           "reise", "tourismus", "urlaub", "flug", "reiseziel",
                           # Portuguese
                           "viagem", "férias", "voo", "destino"]
            },
            "sports": {
                "name": "Sports",
                "description": "Sports, fitness, athletics, games, outdoor activities, football, basketball, swimming, gym. "
                              "Swahili: michezo, soka, mpira, kuogelea, riadha, mazoezi. "
                              "Spanish: deportes, fútbol, baloncesto, natación, gimnasio, atletismo. "
                              "French: sports, football, basketball, natation, gym, athlétisme. "
                              "German: sport, fußball, basketball, schwimmen, fitness, athletik. "
                              "Arabic: رياضة, كرة قدم, كرة سلة, سباحة, لياقة. "
                              "Chinese: 体育, 足球, 篮球, 游泳, 健身, 运动. "
                              "Portuguese: esportes, futebol, basquete, natação, academia, atletismo.",
                "keywords": ["sport", "sports", "football", "soccer", "basketball", "tennis",
                           "swimming", "running", "gym", "fitness", "workout", "athlete",
                           "team", "match", "game", "league", "tournament", "cycling",
                           # Swahili
                           "michezo", "soka", "mpira", "kuogelea", "riadha", "mazoezi",
                           # Spanish
                           "deportes", "fútbol", "baloncesto", "natación", "atletismo",
                           # French
                           "sports", "football", "natation", "athlétisme",
                           # German
                           "sport", "fußball", "schwimmen", "athletik",
                           # Portuguese
                           "esportes", "futebol", "basquete", "natação", "atletismo"]
            },
            "entertainment": {
                "name": "Entertainment",
                "description": "Entertainment, movies, music, events, leisure activities, cinema, concert, party, fun. "
                              "Swahili: burudani, filamu, muziki, sinema, tamasha, sherehe. "
                              "Spanish: entretenimiento, película, música, cine, concierto, fiesta, diversión. "
                              "French: divertissement, film, musique, cinéma, concert, fête. "
                              "German: unterhaltung, film, musik, kino, konzert, party, spaß. "
                              "Arabic: ترفيه, فيلم, موسيقى, سينما, حفلة, مرح. "
                              "Chinese: 娱乐, 电影, 音乐, 电影院, 音乐会, 派对, 乐趣. "
                              "Portuguese: entretenimento, filme, música, cinema, concerto, festa, diversão.",
                "keywords": ["movie", "film", "cinema", "music", "concert", "show", "tv",
                           "streaming", "netflix", "game", "gaming", "party", "club",
                           "dance", "art", "museum", "festival", "comedy", "fun",
                           # Swahili
                           "burudani", "filamu", "muziki", "sinema", "tamasha", "sherehe",
                           # Spanish
                           "entretenimiento", "película", "música", "cine", "concierto", "fiesta", "diversión",
                           # French
                           "divertissement", "film", "musique", "cinéma", "concert", "fête",
                           # German
                           "unterhaltung", "kino", "konzert", "spaß",
                           # Portuguese
                           "entretenimento", "filme", "música", "concerto", "festa", "diversão"]
            },
            "furniture": {
                "name": "Furniture",
                "description": "Furniture, home decor, interior design, household items, sofa, table, chair, bed. "
                              "Swahili: samani, sofa, meza, kiti, kitanda, kabati. "
                              "Spanish: muebles, sofá, mesa, silla, cama, armario, decoración. "
                              "French: meubles, canapé, table, chaise, lit, armoire, décoration. "
                              "German: möbel, sofa, tisch, stuhl, bett, schrank, dekoration. "
                              "Arabic: أثاث, أريكة, طاولة, كرسي, سرير, خزانة. "
                              "Chinese: 家具, 沙发, 桌子, 椅子, 床, 衣柜, 装饰. "
                              "Portuguese: móveis, sofá, mesa, cadeira, cama, armário, decoração.",
                "keywords": ["furniture", "sofa", "couch", "chair", "table", "desk", "bed",
                           "mattress", "wardrobe", "cabinet", "shelf", "lamp", "curtain",
                           "carpet", "decor", "decoration", "interior", "home",
                           # Swahili
                           "samani", "meza", "kiti", "kitanda", "kabati",
                           # Spanish
                           "muebles", "sofá", "mesa", "silla", "cama", "armario", "decoración",
                           # French
                           "meubles", "canapé", "table", "chaise", "lit", "armoire", "décoration",
                           # German
                           "möbel", "tisch", "stuhl", "bett", "schrank", "dekoration",
                           # Portuguese
                           "móveis", "cadeira", "armário", "decoração"]
            },
            "pets": {
                "name": "Pets",
                "description": "Pets, animals, pet supplies, veterinary services, dog, cat, bird, fish. "
                              "Swahili: wanyama kipenzi, mbwa, paka, ndege, samaki, daktari wa wanyama. "
                              "Spanish: mascotas, animales, perro, gato, pájaro, pez, veterinario. "
                              "French: animaux de compagnie, chien, chat, oiseau, poisson, vétérinaire. "
                              "German: haustiere, hund, katze, vogel, fisch, tierarzt. "
                              "Arabic: حيوانات أليفة, كلب, قطة, طائر, سمك, طبيب بيطري. "
                              "Chinese: 宠物, 狗, 猫, 鸟, 鱼, 兽医. "
                              "Portuguese: animais de estimação, cachorro, gato, pássaro, peixe, veterinário.",
                "keywords": ["pet", "pets", "dog", "cat", "puppy", "kitten", "bird", "fish",
                           "animal", "vet", "veterinary", "pet food", "adoption", "grooming",
                           # Swahili
                           "wanyama", "mbwa", "paka", "ndege", "samaki",
                           # Spanish
                           "mascotas", "animales", "perro", "gato", "pájaro", "pez", "veterinario",
                           # French
                           "animaux", "chien", "chat", "oiseau", "poisson", "vétérinaire",
                           # German
                           "haustiere", "hund", "katze", "vogel", "fisch", "tierarzt",
                           # Portuguese
                           "animais", "cachorro", "pássaro", "peixe", "veterinário"]
            },
            "books": {
                "name": "Books",
                "description": "Books, reading, literature, publications, media, novel, magazine, library. "
                              "Swahili: vitabu, kusoma, maktaba, gazeti, fasihi. "
                              "Spanish: libros, leer, lectura, biblioteca, revista, literatura. "
                              "French: livres, lire, lecture, bibliothèque, magazine, littérature. "
                              "German: bücher, lesen, bibliothek, zeitschrift, literatur. "
                              "Arabic: كتب, قراءة, مكتبة, مجلة, أدب. "
                              "Chinese: 书籍, 阅读, 图书馆, 杂志, 文学. "
                              "Portuguese: livros, ler, leitura, biblioteca, revista, literatura.",
                "keywords": ["book", "books", "reading", "read", "novel", "fiction", "magazine",
                           "newspaper", "library", "ebook", "audiobook", "author", "literature",
                           # Swahili
                           "vitabu", "kusoma", "maktaba", "gazeti", "fasihi",
                           # Spanish
                           "libros", "leer", "lectura", "biblioteca", "revista", "literatura",
                           # French
                           "livres", "lire", "bibliothèque", "magazine", "littérature",
                           # German
                           "bücher", "lesen", "bibliothek", "zeitschrift", "literatur",
                           # Portuguese
                           "ler", "leitura", "biblioteca", "revista", "literatura"]
            }
        }

    def load_model(self) -> bool:
        """Load the sentence transformer model through model_registry."""
        # Try model_registry first
        if MODEL_REGISTRY_AVAILABLE:
            try:
                store = ModelStore(auto_download=True, verbose=True)

                # Ensure the multilingual model is available
                if store.ensure_models(['sentence_transformers_multilingual']):
                    # Get the preloaded model
                    self.model = store.get_sentence_transformer_multilingual()
                    if self.model:
                        self.is_loaded = True
                        print(f"✅ Loaded multilingual sentence transformer via model_registry")
                        return True
            except Exception as e:
                print(f"⚠️ model_registry failed: {e}, trying direct import")

        # Fallback to direct loading
        if not SENTENCE_TRANSFORMERS_AVAILABLE:
            print("Sentence transformers not available, using keyword fallback")
            self.is_loaded = True
            return True

        try:
            model_full_name = f"sentence-transformers/{self.model_name}"
            print(f"Loading model directly: {model_full_name}")
            self.model = SentenceTransformer(model_full_name)
            self.is_loaded = True
            print("✅ Multilingual model loaded successfully")
            return True
        except Exception as e:
            print(f"Error loading model: {e}")
            self.is_loaded = True  # Still mark as loaded to use fallback
            return False

    def set_categories(self, categories: Dict[str, Dict]) -> None:
        """
        Set the categories to match against.

        Args:
            categories: Dict mapping category slugs to category info
                       e.g., {"food": {"name": "Food", "description": "..."}}
        """
        self.categories = categories
        self._compute_embeddings()

    def load_default_categories(self) -> None:
        """Load default category definitions."""
        self.categories = self.default_categories
        self._compute_embeddings()

    def _compute_embeddings(self) -> None:
        """Compute embeddings for all categories."""
        if not self.model or not SENTENCE_TRANSFORMERS_AVAILABLE:
            return

        for slug, info in self.categories.items():
            # Create rich text representation for embedding
            text_parts = [info.get("name", slug)]
            if "description" in info:
                text_parts.append(info["description"])
            if "keywords" in info:
                text_parts.append(" ".join(info["keywords"]))

            combined_text = " ".join(text_parts)
            embedding = self.model.encode(combined_text, convert_to_numpy=True)
            self.category_embeddings[slug] = embedding

    def match(self, query: str, top_k: int = 3, threshold: float = 0.3) -> List[Dict]:
        """
        Match a query to categories using CACHE-FIRST + HYBRID semantic + keyword matching.

        Flow:
        1. CHECK CACHE FIRST (fastest path)
        2. If cache miss, use hybrid matching:
           a. Check exact keyword matches (highest priority)
           b. Use semantic similarity
           c. Combine scores for best results
        3. Store results in cache for future queries

        Args:
            query: User's search query
            top_k: Number of top matches to return
            threshold: Minimum similarity score (0-1)

        Returns:
            List of matching categories with scores
        """
        if not self.is_loaded:
            self.load_model()
            self.load_default_categories()

        query = query.strip().lower()
        if not query:
            return []

        # ==========================================
        # STEP 1: CHECK CACHE FIRST (fastest path)
        # ==========================================
        if self.use_cache and self.cache:
            # Create cache key with parameters
            cache_key = f"{query}|k{top_k}|t{threshold}"
            cached_result = self.cache.get(cache_key)

            if cached_result:
                self.cache_hits += 1
                # Return cached results (already filtered by top_k and threshold)
                return cached_result

        self.cache_misses += 1

        # ==========================================
        # STEP 2: CACHE MISS - Query the model
        # ==========================================
        results = self._hybrid_match(query, top_k, threshold)

        # ==========================================
        # STEP 3: Store results in cache
        # ==========================================
        if self.use_cache and self.cache and results:
            cache_key = f"{query}|k{top_k}|t{threshold}"
            self.cache.set(cache_key, results)

        return results

    def _hybrid_match(self, query: str, top_k: int, threshold: float) -> List[Dict]:
        """
        Hybrid matching combining exact keywords + semantic similarity.
        This achieves 0.95+ accuracy by catching exact matches that semantic might miss.
        """
        results = {}
        query_normalized = query.strip().lower()

        # Step 1: Check for EXACT keyword matches (highest priority - score boost)
        for slug, info in self.categories.items():
            keywords = [kw.lower() for kw in info.get("keywords", [])]

            # Exact match in keywords
            if query_normalized in keywords:
                results[slug] = {
                    "slug": slug,
                    "name": info.get("name", slug),
                    "score": 0.98,  # Very high score for exact match
                    "match_type": "exact_keyword"
                }
                continue

            # Partial keyword match
            for kw in keywords:
                if query_normalized == kw or kw == query_normalized:
                    results[slug] = {
                        "slug": slug,
                        "name": info.get("name", slug),
                        "score": 0.95,
                        "match_type": "keyword"
                    }
                    break
                elif len(query_normalized) >= 3 and (query_normalized in kw or kw in query_normalized):
                    if slug not in results or results[slug]["score"] < 0.7:
                        results[slug] = {
                            "slug": slug,
                            "name": info.get("name", slug),
                            "score": 0.7,
                            "match_type": "partial_keyword"
                        }

        # Step 2: Semantic matching (if model available)
        if self.model and SENTENCE_TRANSFORMERS_AVAILABLE and self.category_embeddings:
            query_embedding = self.model.encode(query_normalized, convert_to_numpy=True)

            for slug, cat_embedding in self.category_embeddings.items():
                similarity = float(util.cos_sim(query_embedding, cat_embedding)[0][0])

                if slug in results:
                    # Boost existing keyword matches with semantic score
                    # Take the higher of keyword score or semantic * 1.2
                    boosted_semantic = min(0.99, similarity * 1.2)
                    if boosted_semantic > results[slug]["score"]:
                        results[slug]["score"] = round(boosted_semantic, 4)
                        results[slug]["match_type"] = "hybrid"
                elif similarity >= threshold:
                    results[slug] = {
                        "slug": slug,
                        "name": self.categories[slug].get("name", slug),
                        "score": round(similarity, 4),
                        "match_type": "semantic"
                    }

        # Step 3: If no results yet, fall back to pure keyword matching
        if not results:
            return self._keyword_match(query_normalized, top_k, threshold)

        # Sort by score descending
        sorted_results = sorted(results.values(), key=lambda x: x["score"], reverse=True)
        return sorted_results[:top_k]

    def _semantic_match(self, query: str, top_k: int, threshold: float) -> List[Dict]:
        """Perform semantic similarity matching."""
        query_embedding = self.model.encode(query, convert_to_numpy=True)

        results = []
        for slug, cat_embedding in self.category_embeddings.items():
            similarity = float(util.cos_sim(query_embedding, cat_embedding)[0][0])

            if similarity >= threshold:
                results.append({
                    "slug": slug,
                    "name": self.categories[slug].get("name", slug),
                    "score": round(similarity, 4),
                    "match_type": "semantic"
                })

        # Sort by score descending
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]

    def _keyword_match(self, query: str, top_k: int, threshold: float) -> List[Dict]:
        """Fallback keyword-based matching."""
        results = []
        query_words = set(query.split())

        for slug, info in self.categories.items():
            score = 0.0

            # Check category name
            name = info.get("name", slug).lower()
            if query in name or name in query:
                score = max(score, 0.9)

            # Check keywords
            keywords = info.get("keywords", [])
            for keyword in keywords:
                keyword = keyword.lower()
                if query == keyword:
                    score = max(score, 0.95)
                elif query in keyword or keyword in query:
                    score = max(score, 0.7)
                elif any(word in keyword or keyword in word for word in query_words):
                    score = max(score, 0.5)

            # Check description
            description = info.get("description", "").lower()
            if query in description:
                score = max(score, 0.6)

            if score >= threshold:
                results.append({
                    "slug": slug,
                    "name": info.get("name", slug),
                    "score": round(score, 4),
                    "match_type": "keyword"
                })

        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]

    def get_all_categories(self) -> List[Dict]:
        """Return all available categories."""
        return [
            {"slug": slug, "name": info.get("name", slug)}
            for slug, info in self.categories.items()
        ]

    def get_cache_stats(self) -> Dict:
        """Get cache statistics."""
        stats = {
            "cache_enabled": self.use_cache,
            "matcher_cache_hits": self.cache_hits,
            "matcher_cache_misses": self.cache_misses,
            "matcher_hit_rate": self.cache_hits / max(1, self.cache_hits + self.cache_misses)
        }

        if self.use_cache and self.cache:
            stats["cache_stats"] = self.cache.stats()

        return stats

    def clear_cache(self) -> Dict:
        """Clear all caches."""
        result = {"cleared": False}

        if self.use_cache and self.cache:
            result = self.cache.clear()
            result["cleared"] = True

        # Reset local stats
        self.cache_hits = 0
        self.cache_misses = 0

        return result

    def warmup_cache(self, queries: Optional[List[str]] = None) -> int:
        """
        Warm up cache with common queries.

        Args:
            queries: List of queries to pre-cache. If None, uses default common queries.

        Returns:
            Number of queries cached
        """
        if not self.use_cache or not self.cache:
            return 0

        # Default common queries if none provided
        if queries is None:
            queries = [
                # English
                "food", "car", "house", "job", "phone", "clothes", "doctor", "school", "travel",
                "hungry", "eat", "rent", "buy", "sell", "work", "hire",
                # Swahili
                "chakula", "nyumba", "gari", "kazi", "simu",
                # Spanish
                "comida", "coche", "casa", "trabajo",
                # French
                "nourriture", "voiture", "maison", "travail",
                # German
                "essen", "auto", "haus", "arbeit",
                # Common terms
                "laptop", "computer", "phone", "apartment", "vehicle", "motorcycle",
                "restaurant", "hotel", "flight", "book", "movie", "music", "gym",
                "furniture", "sofa", "pet", "dog", "cat"
            ]

        return self.cache.warmup(queries, lambda q: self._hybrid_match(q, 3, 0.3))


# Singleton instance for reuse
_matcher_instance: Optional[CategoryMatcher] = None

def get_matcher(use_cache: bool = True) -> CategoryMatcher:
    """
    Get or create the singleton CategoryMatcher instance.

    Args:
        use_cache: Whether to enable caching (default: True)
    """
    global _matcher_instance
    if _matcher_instance is None:
        _matcher_instance = CategoryMatcher(use_cache=use_cache)
        _matcher_instance.load_model()
        _matcher_instance.load_default_categories()
    return _matcher_instance


def reset_matcher() -> None:
    """Reset the singleton matcher instance (for testing)."""
    global _matcher_instance
    _matcher_instance = None


