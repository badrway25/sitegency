"""
Branding & content maps for the importer.

Contains:
- CATEGORY_META: curated category metadata (tagline, description, icon, color)
- CATEGORY_ALIAS: map messy source folder names to friendly category names
- CREATIVE_NAMES: per-category pool of commercially-sounding template names
- TEMPLATE_TAGLINES: persuasive one-liners per category
- DEFAULT_CUSTOM_FIELDS: the universal customization field set applied to all templates
"""

CATEGORY_ALIAS = {
    'Healt-Fitness': 'Fitness',
    'Food&Drink': 'Restaurant',
    'E-Commerce': 'E-Commerce',
    'Real Estate': 'Real Estate',
    'AppLandingPage': 'App Landing',
    'LandingPage': 'Startup',
    'One Page': 'Portfolio',
    'Magazine & News': 'Blog',
    'Photography': 'Portfolio',
    'Resume': 'Portfolio',
    'Personal': 'Portfolio',
    'Seo': 'Technology',
    'WebHosting': 'Technology',
    'Startup': 'Technology',
    'Creative': 'Agency',
    'Directory': 'Technology',
    'JobBoard': 'Technology',
    'InterieurDesigner': 'Architects',
    'Gaming': 'Technology',
    'Music': 'Creative',
    'Transportation': 'Automotive',
    'Travel': 'Hotel',
    'Event': 'Wedding',
    'Charity': 'Charity',
    'Church': 'Charity',
    'Finance': 'Finance',
    'Gallery': 'Portfolio',
    'Industrial': 'Construction',
    'consulting': 'Agency',
    'Architects': 'Architects',
}


CATEGORY_META = {
    'Animal': {
        'tagline': 'Websites that speak for the voiceless',
        'description': 'Warm, trustworthy templates crafted for veterinary clinics, pet stores, animal shelters and pet-care businesses.',
        'icon': 'bi-heart-pulse',
        'color': '#f97316',
        'order': 10,
        'featured': True,
    },
    'Medical': {
        'tagline': 'Healthcare-grade design, ready out of the box',
        'description': 'Clean, reassuring templates for hospitals, clinics, dentists, and wellness specialists.',
        'icon': 'bi-heart',
        'color': '#06b6d4',
        'order': 20,
        'featured': True,
    },
    'Restaurant': {
        'tagline': 'Serve your brand before the first course',
        'description': 'Appetizing templates for restaurants, cafés, bakeries, food trucks and gourmet experiences.',
        'icon': 'bi-egg-fried',
        'color': '#dc2626',
        'order': 30,
        'featured': True,
    },
    'Beauty': {
        'tagline': 'Elegant digital presence for beauty professionals',
        'description': 'Refined templates for salons, spas, makeup artists, stylists and wellness studios.',
        'icon': 'bi-gem',
        'color': '#ec4899',
        'order': 40,
    },
    'Barber': {
        'tagline': 'Sharp templates for modern barbershops',
        'description': 'Bold, masculine templates tailored to barbershops and men\'s grooming studios.',
        'icon': 'bi-scissors',
        'color': '#1f2937',
        'order': 50,
    },
    'Fitness': {
        'tagline': 'Websites as powerful as your workouts',
        'description': 'High-energy templates for gyms, personal trainers, yoga studios, and wellness centers.',
        'icon': 'bi-lightning-charge',
        'color': '#10b981',
        'order': 60,
        'featured': True,
    },
    'Real Estate': {
        'tagline': 'Open the door to premium real estate websites',
        'description': 'Sophisticated templates for agencies, agents, property listings, and luxury real estate.',
        'icon': 'bi-house-door',
        'color': '#0ea5e9',
        'order': 70,
        'featured': True,
    },
    'Education': {
        'tagline': 'Educational platforms that inspire learning',
        'description': 'Modern templates for schools, universities, online courses, and learning platforms.',
        'icon': 'bi-mortarboard',
        'color': '#6366f1',
        'order': 80,
    },
    'Agency': {
        'tagline': 'Agency-grade templates for creative studios',
        'description': 'Bold and creative templates for digital agencies, studios, and creative professionals.',
        'icon': 'bi-palette',
        'color': '#8b5cf6',
        'order': 90,
        'featured': True,
    },
    'Technology': {
        'tagline': 'The future of tech websites, today',
        'description': 'Innovation-driven templates for SaaS, startups, software houses, and tech brands.',
        'icon': 'bi-cpu',
        'color': '#0ea5e9',
        'order': 100,
        'featured': True,
    },
    'Lawyer': {
        'tagline': 'Authority, trust, and precision in every pixel',
        'description': 'Professional templates for law firms, attorneys, consultants, and legal practices.',
        'icon': 'bi-bank',
        'color': '#1e3a8a',
        'order': 110,
    },
    'Construction': {
        'tagline': 'Build your digital presence with solid foundations',
        'description': 'Industrial templates for construction companies, architects, and building contractors.',
        'icon': 'bi-bricks',
        'color': '#f59e0b',
        'order': 120,
    },
    'Architects': {
        'tagline': 'Blueprints for award-winning studios',
        'description': 'Minimalist templates for architecture studios and interior designers.',
        'icon': 'bi-building',
        'color': '#111827',
        'order': 125,
    },
    'Automotive': {
        'tagline': 'High-performance websites for the auto industry',
        'description': 'Sleek templates for car dealerships, auto repair shops, and automotive brands.',
        'icon': 'bi-car-front',
        'color': '#dc2626',
        'order': 130,
    },
    'Hotel': {
        'tagline': 'Luxury hospitality, elegantly presented online',
        'description': 'Premium templates for hotels, resorts, bed & breakfasts, and hospitality brands.',
        'icon': 'bi-building-check',
        'color': '#92400e',
        'order': 140,
        'featured': True,
    },
    'Wedding': {
        'tagline': 'Celebrate love with unforgettable websites',
        'description': 'Romantic templates for wedding planners, venues, and engagement events.',
        'icon': 'bi-heart-fill',
        'color': '#db2777',
        'order': 150,
    },
    'Portfolio': {
        'tagline': 'Showcase your work like the professional you are',
        'description': 'Minimal, portfolio-focused templates for creatives, freelancers and personal brands.',
        'icon': 'bi-person-workspace',
        'color': '#6366f1',
        'order': 160,
        'featured': True,
    },
    'Business': {
        'tagline': 'Corporate elegance, startup energy',
        'description': 'Versatile business templates for corporations, consultancies and enterprise brands.',
        'icon': 'bi-briefcase',
        'color': '#0f172a',
        'order': 170,
    },
    'E-Commerce': {
        'tagline': 'Sell more with conversion-ready storefronts',
        'description': 'High-converting templates for online stores, fashion boutiques and digital shops.',
        'icon': 'bi-bag',
        'color': '#f97316',
        'order': 180,
    },
    'Finance': {
        'tagline': 'Financial services websites built on trust',
        'description': 'Professional templates for banks, fintech startups, advisors and investment firms.',
        'icon': 'bi-graph-up-arrow',
        'color': '#047857',
        'order': 190,
    },
    'Fashion': {
        'tagline': 'Runway-ready websites for fashion brands',
        'description': 'Editorial templates for fashion designers, boutiques, stylists and models.',
        'icon': 'bi-bag-heart',
        'color': '#be185d',
        'order': 200,
    },
    'Blog': {
        'tagline': 'Publishing platforms that readers love',
        'description': 'Editorial templates for blogs, magazines, news sites and personal publications.',
        'icon': 'bi-journal-richtext',
        'color': '#7c3aed',
        'order': 210,
    },
    'Charity': {
        'tagline': 'Websites that move people to act',
        'description': 'Heartfelt templates for non-profits, charities, churches, and community initiatives.',
        'icon': 'bi-people',
        'color': '#be123c',
        'order': 220,
    },
    'App Landing': {
        'tagline': 'Launch your app with a killer first impression',
        'description': 'Conversion-optimized landing templates for mobile apps, SaaS products and launches.',
        'icon': 'bi-phone',
        'color': '#7c3aed',
        'order': 230,
    },
    'Creative': {
        'tagline': 'For brands that refuse to be boring',
        'description': 'Unconventional templates for creative studios, artists, and visionary brands.',
        'icon': 'bi-stars',
        'color': '#db2777',
        'order': 240,
    },
}


# Creative, commercial names per category — feels like a curated catalog
CREATIVE_NAMES = {
    'animal': ['DogLife', 'PetCare Pro', 'VetNova', 'PawCenter', 'Animalis',
               'CareTail', 'PawStudio', 'WildNest', 'VetAura', 'PetSphere',
               'FurBond', 'PetHarbor'],
    'medical': ['MediCore', 'HealFirst', 'PulseMed', 'CareNest', 'VitaClinic',
                'DentAura', 'Medilux', 'WellPath', 'Clinova', 'BioCare',
                'HealthSphere', 'VitalSign'],
    'restaurant': ['Saveur', 'Gustora', 'TableCraft', 'ForkHaus', 'Umami',
                   'Nourish', 'CulinaryCo', 'TasteFolk', 'Brasserie', 'Bistronomy',
                   'Palato', 'CraveKitchen'],
    'beauty': ['Lumière', 'BelleSpa', 'GlowStudio', 'Eterna', 'Aurae',
               'Velvet', 'Opaline', 'Seraphine', 'SkinHaus', 'BloomBeauty'],
    'barber': ['Iron Razor', 'OakBarber', 'SharpLine', 'Trimwood', 'BarberCraft',
               'CutRoom', 'MaverickCuts', 'Blackbeard', 'NorthBarber', 'ShearCo'],
    'fitness': ['IronForge', 'PulseGym', 'FlexHaus', 'Vitality', 'KineticCo',
                'LiftLab', 'YogaGrove', 'PrimeBody', 'Stamina', 'EnduraFit'],
    'real-estate': ['Estatelux', 'HavenPro', 'PropertyNest', 'CasaRoyale', 'UrbanKey',
                    'BrickBond', 'Domicile', 'Marqueur', 'AbodeOne', 'Terrano'],
    'education': ['LearnSphere', 'Academix', 'EduPulse', 'KnowHub', 'ScholarNest',
                  'BrightPath', 'Mentora', 'StudyForge', 'CampusCore', 'Learnly'],
    'agency': ['Stardom Studio', 'Northlight', 'Parallax', 'Kairos', 'Vantage',
               'Monolith', 'Blueprint', 'IronQuill', 'Fluxwork', 'Emberlane'],
    'technology': ['Hypernova', 'Quantix', 'Cortex', 'Pixelbit', 'Devlane',
                   'Synthesis', 'ByteForge', 'Nebulon', 'Kernelink', 'Stackwise'],
    'lawyer': ['Lex Regalia', 'Counselis', 'Juristica', 'LawForge', 'Veredictum',
               'Noble Counsel', 'Praetor', 'LegalCrest', 'AdvocateHaus'],
    'construction': ['BuildForge', 'Ironworks', 'Constructa', 'BlueBeam', 'Bedrock',
                     'FoundryCo', 'Masonic', 'BuildSphere', 'GraniteCore'],
    'architects': ['Archetype', 'Studiolume', 'Plano', 'Monocle', 'Linework',
                   'Formwise', 'Draftly', 'Arcon'],
    'automotive': ['MotorCore', 'RedLine', 'AutoNova', 'GearHaus', 'Velocita',
                   'DriveForge', 'TurboPoint', 'AxelCo'],
    'hotel': ['Solena', 'Grand Riviera', 'MaisonRoyale', 'Lumen Suites', 'Azzuro',
              'Villanova', 'Resortium', 'BelleRive', 'Casa Serena'],
    'wedding': ['EverAfter', 'Aurelia Weddings', 'VowCraft', 'LumenLove', 'Ceremony Co',
                'Eterna Love', 'Confetto', 'BelleNuit'],
    'portfolio': ['Silhouette', 'Mirror', 'Opuscule', 'Personafolio', 'Monoline',
                  'Rhea', 'Lumina', 'Folio Noir', 'Essentialia', 'Glyph'],
    'business': ['Axiom Corp', 'North Bureau', 'Civitas', 'Prime Office', 'Corporis',
                 'IronDesk', 'Consular', 'Meridia'],
    'e-commerce': ['ShopLuxe', 'KartNova', 'Buysphere', 'Vendura', 'Emporia',
                   'MarketCraft', 'StoreForge', 'Carta'],
    'finance': ['Capitex', 'WealthNova', 'TrustLedger', 'PrimeCapital', 'Fintora',
                'EquitySphere', 'BondForge'],
    'fashion': ['Maison Noir', 'Atelierium', 'VogueLine', 'Couturae', 'Silhouette Co',
                'ModaPrima', 'Velours'],
    'blog': ['InkStory', 'Narrativa', 'Columnist', 'Quillhaus', 'Dispatch',
             'Editoria', 'Margin'],
    'charity': ['HopeFund', 'GiveCircle', 'KindheartCo', 'HandsOn', 'Solidara',
                'Lightpath', 'CareBridge'],
    'app-landing': ['Appulse', 'LaunchPad', 'Tapwise', 'Screenly', 'Bolton',
                    'Appforge'],
    'creative': ['StudioKaleido', 'Vividum', 'Palette Noir', 'Inkwell', 'Pigmento'],
}


TEMPLATE_TAGLINES = {
    'default': [
        'Launch a premium website in minutes, fully branded with your data.',
        'Customize every pixel, preview it live, ship it today.',
        'Hand-crafted design, dynamically yours.',
        'A professional web presence — without the agency price tag.',
    ],
    'animal': [
        'Warm, welcoming digital care for every furry client.',
        'Built for clinics that treat pets like family.',
        'Compassionate design for modern pet professionals.',
    ],
    'medical': [
        'Clinical clarity meets premium design.',
        'Inspire trust before patients walk through the door.',
        'Clean, calm, HIPAA-aware layouts for medical brands.',
    ],
    'restaurant': [
        'Menus, reservations, and ambience — deliciously online.',
        'Bring your kitchen\'s character to the web.',
        'The digital equivalent of a Michelin welcome.',
    ],
    'fitness': [
        'Fuel your fitness brand with a high-energy website.',
        'Built for trainers, studios, and athletic brands.',
        'Every section optimized to convert visitors into members.',
    ],
    'real-estate': [
        'Premium listings deserve premium presentation.',
        'Turn prospects into owners with confidence-driven design.',
    ],
    'agency': [
        'A portfolio-grade showcase for your creative firm.',
        'Bold, award-worthy layouts that sell your studio.',
    ],
    'hotel': [
        'Whisper luxury from the very first scroll.',
        'Boutique hospitality design, premium by default.',
    ],
    'technology': [
        'The startup-grade launchpad your product deserves.',
        'Engineered for SaaS, built for conversions.',
    ],
    'portfolio': [
        'Your work, framed like a gallery wall.',
        'Minimal, magnetic, unmistakably you.',
    ],
}


# Universal customization fields applied to every imported template.
# The live customizer maps these to template elements via JS selectors.
DEFAULT_CUSTOM_FIELDS = [
    # BRANDING
    {'key': 'brand_name', 'label': 'Business Name', 'type': 'text', 'group': 'branding',
     'placeholder': 'e.g. Dr. Smith Veterinary', 'required': True},
    {'key': 'brand_logo', 'label': 'Logo', 'type': 'image', 'group': 'branding'},
    {'key': 'brand_favicon', 'label': 'Favicon', 'type': 'image', 'group': 'branding'},
    {'key': 'brand_tagline', 'label': 'Tagline / Payoff', 'type': 'text', 'group': 'branding',
     'placeholder': 'e.g. Caring for pets since 1998'},

    # COLORS
    {'key': 'color_primary', 'label': 'Primary Color', 'type': 'color',
     'group': 'colors', 'default': '#6366f1'},
    {'key': 'color_secondary', 'label': 'Secondary Color', 'type': 'color',
     'group': 'colors', 'default': '#ec4899'},
    {'key': 'color_accent', 'label': 'Accent Color', 'type': 'color',
     'group': 'colors', 'default': '#10b981'},

    # HERO
    {'key': 'hero_title', 'label': 'Hero Title', 'type': 'text', 'group': 'hero',
     'placeholder': 'e.g. Caring for every tail that wags'},
    {'key': 'hero_subtitle', 'label': 'Hero Subtitle', 'type': 'textarea', 'group': 'hero'},
    {'key': 'hero_image', 'label': 'Hero Image', 'type': 'image', 'group': 'hero'},
    {'key': 'hero_cta_label', 'label': 'Hero Button Text', 'type': 'text', 'group': 'hero',
     'placeholder': 'Book an Appointment'},
    {'key': 'hero_cta_url', 'label': 'Hero Button URL', 'type': 'url', 'group': 'hero'},

    # ABOUT
    {'key': 'about_title', 'label': 'About Title', 'type': 'text', 'group': 'content'},
    {'key': 'about_text', 'label': 'About Text', 'type': 'textarea', 'group': 'content'},
    {'key': 'about_image', 'label': 'About Image', 'type': 'image', 'group': 'content'},

    # CONTACT
    {'key': 'contact_email', 'label': 'Contact Email', 'type': 'email', 'group': 'contact'},
    {'key': 'contact_phone', 'label': 'Contact Phone', 'type': 'phone', 'group': 'contact'},
    {'key': 'contact_address', 'label': 'Address', 'type': 'textarea', 'group': 'contact'},
    {'key': 'contact_hours', 'label': 'Opening Hours', 'type': 'textarea', 'group': 'contact'},

    # SOCIAL
    {'key': 'social_facebook', 'label': 'Facebook URL', 'type': 'url', 'group': 'social'},
    {'key': 'social_instagram', 'label': 'Instagram URL', 'type': 'url', 'group': 'social'},
    {'key': 'social_twitter', 'label': 'Twitter / X URL', 'type': 'url', 'group': 'social'},
    {'key': 'social_linkedin', 'label': 'LinkedIn URL', 'type': 'url', 'group': 'social'},

    # FOOTER
    {'key': 'footer_copyright', 'label': 'Footer Copyright', 'type': 'text', 'group': 'footer',
     'default': '© Your Business. All rights reserved.'},
]
