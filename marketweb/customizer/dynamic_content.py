"""
Locale-aware dynamic content resolver for Sitegency.

The database stores English taglines and descriptions. When a user switches
language, we need to serve localized equivalents without duplicating every
record. This module provides curated content pools for:

- category taglines & descriptions
- template taglines (deterministic per template via hash)
- template "about this template" descriptions (smart, sector-specific)

Each template gets a DIFFERENT "about" text so the marketplace doesn't read
as copy-paste. Pools are indexed deterministically by slug so the same
template always shows the same copy in a given locale.
"""
from __future__ import annotations

# ================================================================
# LOCALIZED CATEGORY NAMES
# Category.name is stored in English. This map returns a locale-aware
# display name used in navbar, breadcrumbs, listings, etc.
# ================================================================
CATEGORY_NAMES = {
    'Animal':       {'it': 'Animali',        'fr': 'Animaux',         'ar': 'الحيوانات'},
    'Medical':      {'it': 'Medico',         'fr': 'Médical',         'ar': 'الطبي'},
    'Restaurant':   {'it': 'Ristoranti',     'fr': 'Restaurants',     'ar': 'المطاعم'},
    'Hotel':        {'it': 'Hotel',          'fr': 'Hôtels',          'ar': 'الفنادق'},
    'Beauty':       {'it': 'Bellezza',       'fr': 'Beauté',          'ar': 'التجميل'},
    'Barber':       {'it': 'Barbiere',       'fr': 'Barbier',         'ar': 'حلاقة'},
    'Fitness':      {'it': 'Fitness',        'fr': 'Fitness',         'ar': 'اللياقة'},
    'Real Estate':  {'it': 'Immobiliare',    'fr': 'Immobilier',      'ar': 'العقارات'},
    'Education':    {'it': 'Istruzione',     'fr': 'Éducation',       'ar': 'التعليم'},
    'Agency':       {'it': 'Agenzia',        'fr': 'Agence',          'ar': 'الوكالات'},
    'Technology':   {'it': 'Tecnologia',     'fr': 'Technologie',     'ar': 'التقنية'},
    'Lawyer':       {'it': 'Avvocato',       'fr': 'Avocats',         'ar': 'المحاماة'},
    'Construction': {'it': 'Edilizia',       'fr': 'Construction',    'ar': 'البناء'},
    'Architects':   {'it': 'Architetti',     'fr': 'Architectes',     'ar': 'المهندسون المعماريون'},
    'Automotive':   {'it': 'Automotive',     'fr': 'Automobile',      'ar': 'السيارات'},
    'Wedding':      {'it': 'Matrimoni',      'fr': 'Mariage',         'ar': 'الأعراس'},
    'Portfolio':    {'it': 'Portfolio',      'fr': 'Portfolio',       'ar': 'ملفات الأعمال'},
    'Business':     {'it': 'Business',       'fr': 'Entreprise',      'ar': 'الأعمال'},
    'E-Commerce':   {'it': 'E-commerce',     'fr': 'E-commerce',      'ar': 'التجارة الإلكترونية'},
    'Finance':      {'it': 'Finanza',        'fr': 'Finance',         'ar': 'التمويل'},
    'Fashion':      {'it': 'Moda',           'fr': 'Mode',            'ar': 'الأزياء'},
    'Blog':         {'it': 'Blog',           'fr': 'Blog',            'ar': 'المدونة'},
    'Charity':      {'it': 'Beneficenza',    'fr': 'Associations',    'ar': 'الأعمال الخيرية'},
    'App Landing':  {'it': 'App Landing',    'fr': 'App Landing',     'ar': 'صفحات التطبيقات'},
    'Creative':     {'it': 'Creativo',       'fr': 'Créatif',         'ar': 'الإبداعي'},
}


def get_category_name(category, locale='en'):
    """Return locale-aware category name, falling back to the DB value."""
    if not category:
        return ''
    original = getattr(category, 'name', '') or ''
    if locale == 'en' or not locale:
        return original
    trans = CATEGORY_NAMES.get(original, {})
    return trans.get(locale, original)


# ================================================================
# LOCALIZED FAQ POOL
# Database FAQs are stored in English. For each locale we serve a
# curated, fully localized set of 10 Q/A pairs via get_localized_faqs.
# ================================================================
FAQ_POOL = {
    'en': [
        {'q': 'Can I really customize everything before I buy?',
         'a': 'Yes. Every template ships with a live customizer where you can swap your logo, colors, headlines, photos, contact details and social links in real time. The preview updates instantly in your browser — you see exactly what you are getting before you pay a cent.'},
        {'q': 'What exactly am I buying?',
         'a': 'A complete, production-ready website package: HTML, CSS, JavaScript, fonts, images, and all assets. You own the code and the commercial license for one project. Deploy anywhere — your own hosting, Netlify, Vercel, AWS, anywhere.'},
        {'q': 'Do I need to know how to code?',
         'a': 'No. Our live customizer handles logo uploads, color changes, text edits and image swaps without touching code. If you want to dig deeper, the source is yours — clean, documented, and built to modern standards.'},
        {'q': 'How is Sitegency different from other template marketplaces?',
         'a': 'Three things: you can actually navigate every page of a template before buying, you customize with your real data inside our live editor, and every template is curated, refined and modernized in-house.'},
        {'q': 'Why is the marketplace built on Django?',
         'a': 'Django is the gold standard for secure, scalable web platforms. We chose it because your checkout, your customization data and your downloads deserve an enterprise-grade foundation.'},
        {'q': 'What does the license allow?',
         'a': 'A Single Project license lets you deploy the template on one domain for one business or client. Need more? Our Extended and Unlimited licenses cover agencies, freelancers and teams running multiple projects.'},
        {'q': 'Do you offer refunds?',
         'a': 'Yes. Every purchase is protected by a 14-day refund policy. If the template does not meet your expectations, contact support and we make it right — no questions asked.'},
        {'q': 'How long does it take to launch a site?',
         'a': 'Most customers go from browsing to live site in under 60 minutes. Pick a template, drop in your content, download the package, upload to your host.'},
        {'q': 'Do I get updates?',
         'a': 'Yes. Every template includes 6 months of free updates — security patches, browser compatibility fixes, and minor enhancements. Major version upgrades are available at a reduced rate.'},
        {'q': 'Can I preview on mobile?',
         'a': 'Absolutely. Our preview engine and customizer include desktop, tablet and mobile viewports. Every template is responsive by default, rigorously tested across devices.'},
    ],
    'it': [
        {'q': 'Posso davvero personalizzare tutto prima di acquistare?',
         'a': 'Sì. Ogni template include un customizer live dove puoi sostituire logo, colori, titoli, foto, dati di contatto e link social in tempo reale. L anteprima si aggiorna istantaneamente nel browser — vedi esattamente quello che compri prima di pagare un centesimo.'},
        {'q': 'Cosa acquisto esattamente?',
         'a': 'Un pacchetto sito completo pronto alla produzione: HTML, CSS, JavaScript, font, immagini e tutti gli asset. Possiedi il codice e la licenza commerciale per un progetto. Puoi pubblicarlo ovunque — hosting tuo, Netlify, Vercel, AWS, dove vuoi.'},
        {'q': 'Devo saper programmare?',
         'a': 'No. Il customizer live gestisce upload di loghi, cambi di colore, modifiche testo e sostituzioni immagini senza toccare codice. Se vuoi andare più a fondo, il sorgente è tuo — pulito, documentato e costruito con standard moderni.'},
        {'q': 'In cosa Sitegency è diverso dagli altri marketplace di template?',
         'a': 'Tre cose: puoi davvero navigare ogni pagina di un template prima di comprarlo, personalizzi con i tuoi dati reali dentro l editor live, e ogni template è curato, raffinato e modernizzato internamente.'},
        {'q': 'Perché il marketplace è costruito su Django?',
         'a': 'Django è lo standard gold per piattaforme web sicure e scalabili. Lo abbiamo scelto perché checkout, dati di personalizzazione e download meritano una base enterprise-grade.'},
        {'q': 'Cosa permette la licenza?',
         'a': 'La licenza Single Project ti permette di pubblicare il template su un dominio per un azienda o cliente. Ti serve di più? Le licenze Extended e Unlimited coprono agenzie, freelance e team con più progetti attivi.'},
        {'q': 'Offrite rimborsi?',
         'a': 'Sì. Ogni acquisto è protetto da una politica di rimborso di 14 giorni. Se il template non soddisfa le tue aspettative, contatta il supporto e rimediamo — senza fare domande.'},
        {'q': 'Quanto tempo serve per lanciare un sito?',
         'a': 'La maggior parte dei clienti passa dalla ricerca al sito live in meno di 60 minuti. Scegli un template, inserisci i contenuti, scarica il pacchetto, carica sul tuo host.'},
        {'q': 'Ricevo aggiornamenti?',
         'a': 'Sì. Ogni template include 6 mesi di aggiornamenti gratuiti — patch di sicurezza, fix di compatibilità browser e miglioramenti minori. Upgrade di versione maggiore disponibili a prezzo ridotto.'},
        {'q': 'Posso vedere l anteprima su mobile?',
         'a': 'Assolutamente. Il preview engine e il customizer includono viewport desktop, tablet e mobile. Ogni template è responsive di default, testato rigorosamente su tutti i dispositivi.'},
    ],
    'fr': [
        {'q': 'Puis-je vraiment tout personnaliser avant d acheter ?',
         'a': 'Oui. Chaque template inclut un éditeur en direct où vous pouvez changer votre logo, vos couleurs, titres, photos, coordonnées et liens sociaux en temps réel. L aperçu se met à jour instantanément — vous voyez exactement ce que vous achetez avant de payer le moindre centime.'},
        {'q': 'Qu est-ce que j achète exactement ?',
         'a': 'Un paquet de site complet prêt pour la production : HTML, CSS, JavaScript, polices, images et toutes les ressources. Vous possédez le code et la licence commerciale pour un projet. Déployez-le partout — votre hébergeur, Netlify, Vercel, AWS, où vous voulez.'},
        {'q': 'Dois-je savoir coder ?',
         'a': 'Non. Notre éditeur en direct gère les téléversements de logo, les changements de couleur, les modifications de texte et les remplacements d images sans toucher au code. Si vous voulez aller plus loin, le code source est à vous — propre, documenté et construit aux standards modernes.'},
        {'q': 'En quoi Sitegency est-il différent des autres marketplaces de templates ?',
         'a': 'Trois choses : vous pouvez réellement parcourir chaque page d un template avant d acheter, vous personnalisez avec vos vraies données dans notre éditeur en direct, et chaque template est sélectionné, affiné et modernisé en interne.'},
        {'q': 'Pourquoi la marketplace est-elle construite sur Django ?',
         'a': 'Django est la référence pour les plateformes web sécurisées et évolutives. Nous l avons choisi parce que votre paiement, vos données de personnalisation et vos téléchargements méritent des fondations de niveau entreprise.'},
        {'q': 'Que permet la licence ?',
         'a': 'Une licence Single Project vous permet de déployer le template sur un domaine pour une entreprise ou un client. Besoin de plus ? Nos licences Extended et Unlimited couvrent les agences, freelances et équipes gérant plusieurs projets.'},
        {'q': 'Proposez-vous des remboursements ?',
         'a': 'Oui. Chaque achat est protégé par une politique de remboursement de 14 jours. Si le template ne répond pas à vos attentes, contactez le support et nous rectifions — sans poser de questions.'},
        {'q': 'Combien de temps faut-il pour lancer un site ?',
         'a': 'La plupart des clients passent de la navigation au site en ligne en moins de 60 minutes. Choisissez un template, ajoutez vos contenus, téléchargez le paquet, uploadez chez votre hébergeur.'},
        {'q': 'Y a-t-il des mises à jour ?',
         'a': 'Oui. Chaque template inclut 6 mois de mises à jour gratuites — correctifs de sécurité, corrections de compatibilité navigateur et améliorations mineures. Les mises à niveau majeures sont disponibles à tarif réduit.'},
        {'q': 'Puis-je prévisualiser sur mobile ?',
         'a': 'Absolument. Notre moteur d aperçu et notre éditeur incluent les vues desktop, tablette et mobile. Chaque template est responsive par défaut, rigoureusement testé sur tous les appareils.'},
    ],
    'ar': [
        {'q': 'هل يمكنني فعلاً تخصيص كل شيء قبل الشراء؟',
         'a': 'نعم. يأتي كل قالب مع محرّر مباشر حيث يمكنك استبدال شعارك وألوانك وعناوينك وصورك وبيانات الاتصال وروابط التواصل في الوقت الفعلي. تتحدّث المعاينة فوراً في متصفّحك — ترى بالضبط ما تحصل عليه قبل أن تدفع فلساً واحداً.'},
        {'q': 'ماذا أشتري بالضبط؟',
         'a': 'حزمة موقع كاملة جاهزة للإنتاج: HTML و CSS و JavaScript وخطوط وصور وجميع الموارد. تمتلك الكود والترخيص التجاري لمشروع واحد. انشره في أي مكان — استضافتك الخاصة أو Netlify أو Vercel أو AWS، أينما أردت.'},
        {'q': 'هل يجب أن أجيد البرمجة؟',
         'a': 'لا. محرّرنا المباشر يتولّى رفع الشعار وتغيير الألوان وتعديل النصوص واستبدال الصور دون لمس الكود. إذا أردت التعمّق أكثر، فالكود المصدري ملك لك — نظيف وموثَّق ومبني على معايير حديثة.'},
        {'q': 'بماذا تختلف بدرواي عن أسواق القوالب الأخرى؟',
         'a': 'ثلاثة أمور: يمكنك فعلاً تصفّح كل صفحة من القالب قبل الشراء، تخصّص ببياناتك الفعلية داخل محرّرنا المباشر، وكل قالب يُختار ويُصقل ويُحدَّث داخلياً.'},
        {'q': 'لماذا السوق مبني على Django؟',
         'a': 'جانغو هو المعيار الذهبي لمنصّات الويب الآمنة القابلة للتوسّع. اخترناه لأن عملية الدفع وبيانات التخصيص والتنزيلات تستحق أساساً بمستوى المؤسّسات.'},
        {'q': 'ماذا يسمح به الترخيص؟',
         'a': 'ترخيص المشروع الواحد يسمح لك بنشر القالب على نطاق واحد لعمل واحد أو عميل واحد. تحتاج المزيد؟ تراخيصنا الموسَّعة واللامحدودة تغطّي الوكالات والمستقلّين والفِرَق التي تدير مشاريع متعدّدة.'},
        {'q': 'هل تقدّمون استرداد المبلغ؟',
         'a': 'نعم. كل عملية شراء محمية بسياسة استرداد مدّتها 14 يوماً. إذا لم يلبّ القالب توقّعاتك، تواصل مع الدعم وسنصلح الأمر — دون أسئلة.'},
        {'q': 'كم من الوقت يستغرق إطلاق الموقع؟',
         'a': 'معظم العملاء ينتقلون من التصفّح إلى الموقع الحيّ في أقل من 60 دقيقة. اختر قالباً، أضف محتواك، حمّل الحزمة، ارفعها على استضافتك.'},
        {'q': 'هل أحصل على تحديثات؟',
         'a': 'نعم. كل قالب يتضمّن 6 أشهر من التحديثات المجانية — تصحيحات أمنية وإصلاحات توافق المتصفّحات وتحسينات طفيفة. ترقيات الإصدارات الكبرى متاحة بسعر مخفَّض.'},
        {'q': 'هل يمكنني المعاينة على الجوال؟',
         'a': 'بالتأكيد. محرّك المعاينة والمحرّر لدينا يتضمّنان مشاهد سطح المكتب والجهاز اللوحي والجوال. كل قالب متجاوب افتراضياً ومختبَر بصرامة على جميع الأجهزة.'},
    ],
}


def get_localized_faqs(locale='en'):
    """Return the locale-native FAQ list (10 Q/A pairs)."""
    return FAQ_POOL.get(locale, FAQ_POOL['en'])


# ================================================================
# CATEGORIZED FAQ POOL — for the dedicated /faq/ page
# Each entry has: category key + question + answer + popular flag
# ================================================================
FAQ_CATEGORIES = {
    'en': [
        ('getting-started', 'Getting started',         'bi-rocket-takeoff'),
        ('templates',       'Templates & preview',     'bi-grid-3x3-gap'),
        ('licensing',       'Licensing & pricing',     'bi-shield-check'),
        ('customization',   'Customization & support', 'bi-palette2'),
        ('enterprise',      'Enterprise & teams',      'bi-building'),
    ],
    'it': [
        ('getting-started', 'Primi passi',             'bi-rocket-takeoff'),
        ('templates',       'Template e anteprima',    'bi-grid-3x3-gap'),
        ('licensing',       'Licenze e prezzi',        'bi-shield-check'),
        ('customization',   'Personalizzazione e supporto', 'bi-palette2'),
        ('enterprise',      'Enterprise e team',       'bi-building'),
    ],
    'fr': [
        ('getting-started', 'Premiers pas',            'bi-rocket-takeoff'),
        ('templates',       'Templates et aperçu',     'bi-grid-3x3-gap'),
        ('licensing',       'Licences et tarifs',      'bi-shield-check'),
        ('customization',   'Personnalisation et support', 'bi-palette2'),
        ('enterprise',      'Entreprise et équipes',   'bi-building'),
    ],
    'ar': [
        ('getting-started', 'الخطوات الأولى',          'bi-rocket-takeoff'),
        ('templates',       'القوالب والمعاينة',       'bi-grid-3x3-gap'),
        ('licensing',       'التراخيص والتسعير',       'bi-shield-check'),
        ('customization',   'التخصيص والدعم',          'bi-palette2'),
        ('enterprise',      'المؤسسات والفرق',         'bi-building'),
    ],
}


FAQ_CATEGORIZED = {
    'en': [
        # ---- Getting started ----
        {'cat': 'getting-started', 'popular': True,
         'q': 'How exactly does Sitegency work?',
         'a': 'Sitegency is a premium website template marketplace with a twist: you can navigate every page of every template before buying, and customize it live with your own logo, colors, photos and text directly in your browser. When you are ready, checkout takes less than a minute and you download a complete, production-ready package.'},
        {'cat': 'getting-started', 'popular': True,
         'q': 'Do I need to know how to code?',
         'a': 'Absolutely not. Our live customizer handles logo uploads, color changes, text edits and image swaps without a single line of code. If you ever want to dig deeper, the full source is yours — clean, documented, and built to modern standards.'},
        {'cat': 'getting-started',
         'q': 'How long does it take to launch my site?',
         'a': 'Most customers go from browsing to a live website in under 60 minutes. Pick a template, drop in your content through the customizer, download the package, upload to your hosting. That is the entire workflow.'},
        {'cat': 'getting-started',
         'q': 'What is included when I buy a template?',
         'a': 'You receive the complete website package: HTML, CSS, JavaScript, fonts, images and all assets, plus a commercial license for one project. You also get 6 months of free updates and priority email support from our team.'},

        # ---- Templates & preview ----
        {'cat': 'templates', 'popular': True,
         'q': 'Can I really navigate every page before buying?',
         'a': 'Yes. Click Preview on any template and you can browse the homepage, about, services, contact, gallery — every single page exactly as a real visitor would. No locked demos, no misleading screenshots. What you see is what you own.'},
        {'cat': 'templates',
         'q': 'How many templates are available?',
         'a': 'Our catalog currently contains 190+ premium templates across 24 categories, ranging from veterinary clinics and restaurants to SaaS, real estate, wedding planners and creative studios. New templates are added every month.'},
        {'cat': 'templates',
         'q': 'Are the templates responsive and mobile-ready?',
         'a': 'Every template is fully responsive by default and tested on desktop, tablet and mobile viewports. Our customizer even lets you preview your changes in all three device sizes before you purchase.'},
        {'cat': 'templates',
         'q': 'Can I use a template as a starting point for a client project?',
         'a': 'Yes — that is exactly what many of our users do. A Single Project license covers one client domain. For multiple clients, our Extended or Unlimited licenses are the right fit.'},

        # ---- Licensing & pricing ----
        {'cat': 'licensing', 'popular': True,
         'q': 'What does the standard license cover?',
         'a': 'The Single Project license lets you deploy the template on one domain for one business or client. You can modify the code freely, but you cannot resell or redistribute the template itself. For agencies and freelancers working on multiple projects, we offer Extended and Unlimited licenses.'},
        {'cat': 'licensing',
         'q': 'How much does a template cost?',
         'a': 'Templates range from €39 to €89 depending on complexity and page count. Elite-tier templates with advanced interactions start at €79. Every price is one-time — no subscriptions, no hidden fees, no renewal charges.'},
        {'cat': 'licensing',
         'q': 'Do you offer refunds?',
         'a': 'Yes, every purchase is protected by a 14-day refund policy. If the template does not meet your expectations for any reason, contact our support team and we will make it right — no questions asked.'},
        {'cat': 'licensing',
         'q': 'Which payment methods do you accept?',
         'a': 'We accept major credit and debit cards, PayPal, Apple Pay and Google Pay. All payments are processed through PCI-compliant gateways with end-to-end encryption. Enterprise customers can also pay by bank transfer upon request.'},

        # ---- Customization & support ----
        {'cat': 'customization', 'popular': True,
         'q': 'What can I customize in the live editor?',
         'a': 'Logo, brand name, tagline, primary and secondary colors, hero image and text, services, team photos, contact details, social links, footer copyright and more. Every change is applied instantly inside the browser preview.'},
        {'cat': 'customization',
         'q': 'Will I receive updates after purchase?',
         'a': 'Yes. Every template includes 6 months of free updates covering security patches, browser compatibility fixes and minor enhancements. Major version upgrades are offered at a reduced rate for existing customers.'},
        {'cat': 'customization',
         'q': 'What kind of support is included?',
         'a': 'Every purchase includes priority email support with a response time under 24 hours on business days. For enterprise customers, we also offer dedicated account managers and live onboarding calls.'},
        {'cat': 'customization',
         'q': 'Can I change the design after downloading?',
         'a': 'Completely. You own the full source code — HTML, CSS, JavaScript and all assets. Modify, extend or rebuild any part of the template to match your exact needs. Our documentation guides you through every section.'},

        # ---- Enterprise & teams ----
        {'cat': 'enterprise',
         'q': 'Do you offer volume discounts for agencies?',
         'a': 'Yes. Our Extended and Unlimited licenses are designed specifically for agencies and freelancers who build sites for multiple clients. Contact our enterprise team for custom pricing based on your volume.'},
        {'cat': 'enterprise',
         'q': 'Can my team collaborate on the same customization?',
         'a': 'Enterprise plans include shared workspaces where your team can comment, review and approve customizations together before exporting the final package. We also provide role-based access control.'},
        {'cat': 'enterprise',
         'q': 'Is Sitegency suitable for large-scale deployments?',
         'a': 'Absolutely. Our platform is built on Django — the same stack trusted by Instagram, Spotify and Pinterest — and is ready for enterprise SLAs. Contact us to discuss dedicated hosting, custom licensing and white-label options.'},
    ],

    'it': [
        # ---- Primi passi ----
        {'cat': 'getting-started', 'popular': True,
         'q': 'Come funziona esattamente Sitegency?',
         'a': 'Sitegency è un marketplace premium di template per siti web con una particolarità: puoi navigare ogni pagina di ogni template prima di acquistarlo e personalizzarlo dal vivo con il tuo logo, colori, foto e testi direttamente nel browser. Quando sei pronto, il checkout richiede meno di un minuto e scarichi un pacchetto completo pronto alla produzione.'},
        {'cat': 'getting-started', 'popular': True,
         'q': 'Devo saper programmare?',
         'a': 'Assolutamente no. Il nostro customizer live gestisce il caricamento del logo, i cambi di colore, le modifiche di testo e le sostituzioni di immagini senza una singola riga di codice. Se vuoi andare più a fondo, il codice sorgente è tuo — pulito, documentato e costruito secondo standard moderni.'},
        {'cat': 'getting-started',
         'q': 'Quanto tempo serve per lanciare il mio sito?',
         'a': 'La maggior parte dei clienti passa dalla ricerca al sito online in meno di 60 minuti. Scegli un template, inserisci i tuoi contenuti tramite il customizer, scarica il pacchetto, caricalo sul tuo hosting. Questo è l intero workflow.'},
        {'cat': 'getting-started',
         'q': 'Cosa ricevo quando acquisto un template?',
         'a': 'Ricevi il pacchetto completo del sito: HTML, CSS, JavaScript, font, immagini e tutti gli asset, oltre a una licenza commerciale per un progetto. Ottieni anche 6 mesi di aggiornamenti gratuiti e supporto email prioritario dal nostro team.'},

        # ---- Template e anteprima ----
        {'cat': 'templates', 'popular': True,
         'q': 'Posso davvero navigare ogni pagina prima di comprare?',
         'a': 'Sì. Clicca Anteprima su qualunque template e puoi navigare homepage, chi siamo, servizi, contatti, gallery — ogni singola pagina esattamente come farebbe un vero visitatore. Niente demo bloccate, niente screenshot ingannevoli. Quello che vedi è quello che possiedi.'},
        {'cat': 'templates',
         'q': 'Quanti template sono disponibili?',
         'a': 'Il nostro catalogo contiene attualmente oltre 190 template premium in 24 categorie, da cliniche veterinarie e ristoranti a SaaS, immobiliare, wedding planner e studi creativi. Nuovi template vengono aggiunti ogni mese.'},
        {'cat': 'templates',
         'q': 'I template sono responsive e pronti per il mobile?',
         'a': 'Ogni template è completamente responsive di default e testato su viewport desktop, tablet e mobile. Il nostro customizer ti permette anche di vedere in anteprima le tue modifiche in tutti e tre i formati prima dell acquisto.'},
        {'cat': 'templates',
         'q': 'Posso usare un template come base per un progetto cliente?',
         'a': 'Sì — è esattamente quello che fanno molti dei nostri utenti. Una licenza Single Project copre un dominio cliente. Per più clienti, le nostre licenze Extended o Unlimited sono la scelta giusta.'},

        # ---- Licenze e prezzi ----
        {'cat': 'licensing', 'popular': True,
         'q': 'Cosa copre la licenza standard?',
         'a': 'La licenza Single Project ti permette di pubblicare il template su un dominio per un azienda o cliente. Puoi modificare il codice liberamente, ma non puoi rivendere o ridistribuire il template stesso. Per agenzie e freelance con più progetti attivi, offriamo licenze Extended e Unlimited.'},
        {'cat': 'licensing',
         'q': 'Quanto costa un template?',
         'a': 'I template vanno da 39 € a 89 € a seconda della complessità e del numero di pagine. I template di fascia Elite con interazioni avanzate partono da 79 €. Ogni prezzo è una tantum — nessun abbonamento, nessun costo nascosto, nessun rinnovo.'},
        {'cat': 'licensing',
         'q': 'Offrite rimborsi?',
         'a': 'Sì, ogni acquisto è protetto da una politica di rimborso di 14 giorni. Se il template non soddisfa le tue aspettative per qualsiasi motivo, contatta il nostro team di supporto e rimediamo — senza fare domande.'},
        {'cat': 'licensing',
         'q': 'Quali metodi di pagamento accettate?',
         'a': 'Accettiamo le principali carte di credito e debito, PayPal, Apple Pay e Google Pay. Tutti i pagamenti sono elaborati tramite gateway conformi PCI con crittografia end-to-end. I clienti enterprise possono anche pagare via bonifico bancario su richiesta.'},

        # ---- Personalizzazione e supporto ----
        {'cat': 'customization', 'popular': True,
         'q': 'Cosa posso personalizzare nell editor live?',
         'a': 'Logo, nome dell azienda, tagline, colori primari e secondari, immagine e testo dell hero, servizi, foto del team, dati di contatto, link social, copyright del footer e altro. Ogni modifica viene applicata istantaneamente nell anteprima del browser.'},
        {'cat': 'customization',
         'q': 'Riceverò aggiornamenti dopo l acquisto?',
         'a': 'Sì. Ogni template include 6 mesi di aggiornamenti gratuiti che coprono patch di sicurezza, fix di compatibilità browser e miglioramenti minori. Gli upgrade di versione maggiore sono offerti a prezzo ridotto per i clienti esistenti.'},
        {'cat': 'customization',
         'q': 'Che tipo di supporto è incluso?',
         'a': 'Ogni acquisto include supporto email prioritario con un tempo di risposta inferiore alle 24 ore nei giorni lavorativi. Per i clienti enterprise offriamo anche account manager dedicati e chiamate di onboarding live.'},
        {'cat': 'customization',
         'q': 'Posso modificare il design dopo il download?',
         'a': 'Completamente. Possiedi il codice sorgente completo — HTML, CSS, JavaScript e tutti gli asset. Modifica, estendi o ricostruisci qualsiasi parte del template per soddisfare le tue esigenze esatte. La nostra documentazione ti guida attraverso ogni sezione.'},

        # ---- Enterprise e team ----
        {'cat': 'enterprise',
         'q': 'Offrite sconti sui volumi per le agenzie?',
         'a': 'Sì. Le nostre licenze Extended e Unlimited sono progettate specificamente per agenzie e freelance che costruiscono siti per più clienti. Contatta il nostro team enterprise per un prezzo personalizzato in base al tuo volume.'},
        {'cat': 'enterprise',
         'q': 'Il mio team può collaborare sulla stessa personalizzazione?',
         'a': 'I piani enterprise includono workspace condivisi dove il tuo team può commentare, rivedere e approvare le personalizzazioni insieme prima di esportare il pacchetto finale. Forniamo anche controllo degli accessi basato sui ruoli.'},
        {'cat': 'enterprise',
         'q': 'Sitegency è adatto a deployment su larga scala?',
         'a': 'Assolutamente. La nostra piattaforma è costruita su Django — lo stesso stack usato da Instagram, Spotify e Pinterest — ed è pronta per SLA enterprise. Contattaci per discutere hosting dedicato, licenze personalizzate e opzioni white-label.'},
    ],

    'fr': [
        {'cat': 'getting-started', 'popular': True,
         'q': 'Comment fonctionne exactement Sitegency ?',
         'a': 'Sitegency est une marketplace premium de templates de sites web avec une particularité : vous pouvez parcourir chaque page de chaque template avant l achat et le personnaliser en direct avec votre logo, vos couleurs, photos et textes directement dans votre navigateur. Une fois prêt, le paiement prend moins d une minute et vous téléchargez un paquet complet prêt pour la production.'},
        {'cat': 'getting-started', 'popular': True,
         'q': 'Dois-je savoir coder ?',
         'a': 'Absolument pas. Notre éditeur en direct gère les téléversements de logo, les changements de couleur, les modifications de texte et les remplacements d images sans une seule ligne de code. Si vous souhaitez aller plus loin, le code source est à vous — propre, documenté et construit selon des standards modernes.'},
        {'cat': 'getting-started',
         'q': 'Combien de temps faut-il pour lancer mon site ?',
         'a': 'La plupart des clients passent de la navigation à un site en ligne en moins de 60 minutes. Choisissez un template, ajoutez votre contenu via l éditeur, téléchargez le paquet, uploadez-le sur votre hébergeur. Voilà le workflow complet.'},
        {'cat': 'getting-started',
         'q': 'Qu est-ce qui est inclus quand j achète un template ?',
         'a': 'Vous recevez le paquet complet du site : HTML, CSS, JavaScript, polices, images et toutes les ressources, plus une licence commerciale pour un projet. Vous obtenez également 6 mois de mises à jour gratuites et un support email prioritaire de notre équipe.'},

        {'cat': 'templates', 'popular': True,
         'q': 'Puis-je vraiment parcourir chaque page avant l achat ?',
         'a': 'Oui. Cliquez sur Aperçu sur n importe quel template et vous pouvez naviguer l accueil, à propos, services, contact, galerie — chaque page exactement comme un vrai visiteur le ferait. Pas de démos verrouillées, pas de captures trompeuses. Ce que vous voyez est ce que vous possédez.'},
        {'cat': 'templates',
         'q': 'Combien de templates sont disponibles ?',
         'a': 'Notre catalogue contient actuellement plus de 190 templates premium dans 24 catégories, des cliniques vétérinaires et restaurants aux SaaS, immobilier, wedding planners et studios créatifs. De nouveaux templates sont ajoutés chaque mois.'},
        {'cat': 'templates',
         'q': 'Les templates sont-ils responsive et prêts pour mobile ?',
         'a': 'Chaque template est entièrement responsive par défaut et testé sur les viewports desktop, tablette et mobile. Notre éditeur vous permet même de prévisualiser vos modifications dans les trois formats avant l achat.'},
        {'cat': 'templates',
         'q': 'Puis-je utiliser un template comme base pour un projet client ?',
         'a': 'Oui — c est exactement ce que font beaucoup de nos utilisateurs. Une licence Single Project couvre un domaine client. Pour plusieurs clients, nos licences Extended ou Unlimited sont le bon choix.'},

        {'cat': 'licensing', 'popular': True,
         'q': 'Que couvre la licence standard ?',
         'a': 'La licence Single Project vous permet de déployer le template sur un domaine pour une entreprise ou un client. Vous pouvez modifier le code librement, mais vous ne pouvez pas revendre ou redistribuer le template lui-même. Pour les agences et freelances avec plusieurs projets actifs, nous proposons des licences Extended et Unlimited.'},
        {'cat': 'licensing',
         'q': 'Combien coûte un template ?',
         'a': 'Les templates vont de 39 € à 89 € selon la complexité et le nombre de pages. Les templates Elite avec interactions avancées commencent à 79 €. Chaque prix est un paiement unique — pas d abonnement, pas de frais cachés, pas de renouvellement.'},
        {'cat': 'licensing',
         'q': 'Proposez-vous des remboursements ?',
         'a': 'Oui, chaque achat est protégé par une politique de remboursement de 14 jours. Si le template ne répond pas à vos attentes pour une raison quelconque, contactez notre équipe de support et nous rectifions — sans poser de questions.'},
        {'cat': 'licensing',
         'q': 'Quels moyens de paiement acceptez-vous ?',
         'a': 'Nous acceptons les principales cartes bancaires, PayPal, Apple Pay et Google Pay. Tous les paiements sont traités via des passerelles conformes PCI avec chiffrement de bout en bout. Les clients entreprise peuvent également payer par virement bancaire sur demande.'},

        {'cat': 'customization', 'popular': True,
         'q': 'Que puis-je personnaliser dans l éditeur en direct ?',
         'a': 'Logo, nom de l entreprise, slogan, couleurs principales et secondaires, image et texte du hero, services, photos de l équipe, coordonnées, liens sociaux, copyright du footer et plus. Chaque modification est appliquée instantanément dans l aperçu du navigateur.'},
        {'cat': 'customization',
         'q': 'Vais-je recevoir des mises à jour après l achat ?',
         'a': 'Oui. Chaque template inclut 6 mois de mises à jour gratuites couvrant correctifs de sécurité, compatibilité navigateur et améliorations mineures. Les mises à niveau majeures sont proposées à tarif réduit pour les clients existants.'},
        {'cat': 'customization',
         'q': 'Quel type de support est inclus ?',
         'a': 'Chaque achat inclut un support email prioritaire avec un temps de réponse inférieur à 24 heures les jours ouvrés. Pour les clients entreprise, nous proposons également des account managers dédiés et des appels d onboarding en direct.'},
        {'cat': 'customization',
         'q': 'Puis-je modifier le design après le téléchargement ?',
         'a': 'Complètement. Vous possédez le code source complet — HTML, CSS, JavaScript et toutes les ressources. Modifiez, étendez ou reconstruisez n importe quelle partie du template pour répondre à vos besoins exacts. Notre documentation vous guide à travers chaque section.'},

        {'cat': 'enterprise',
         'q': 'Proposez-vous des remises sur volume pour les agences ?',
         'a': 'Oui. Nos licences Extended et Unlimited sont conçues spécifiquement pour les agences et freelances qui construisent des sites pour plusieurs clients. Contactez notre équipe entreprise pour un tarif personnalisé selon votre volume.'},
        {'cat': 'enterprise',
         'q': 'Mon équipe peut-elle collaborer sur la même personnalisation ?',
         'a': 'Les plans entreprise incluent des workspaces partagés où votre équipe peut commenter, revoir et approuver les personnalisations ensemble avant d exporter le paquet final. Nous fournissons également un contrôle d accès basé sur les rôles.'},
        {'cat': 'enterprise',
         'q': 'Sitegency convient-il aux déploiements à grande échelle ?',
         'a': 'Absolument. Notre plateforme est construite sur Django — le même stack utilisé par Instagram, Spotify et Pinterest — et est prête pour les SLA entreprise. Contactez-nous pour discuter hébergement dédié, licences personnalisées et options white-label.'},
    ],

    'ar': [
        {'cat': 'getting-started', 'popular': True,
         'q': 'كيف تعمل بدرواي تحديداً؟',
         'a': 'بدرواي سوق فاخر لقوالب المواقع مع ميزة مختلفة: يمكنك تصفح كل صفحة من كل قالب قبل الشراء وتخصيصه مباشرة بشعارك وألوانك وصورك ونصوصك داخل متصفحك. عندما تكون جاهزاً، يستغرق الدفع أقل من دقيقة، وتحصل على حزمة كاملة جاهزة للإنتاج.'},
        {'cat': 'getting-started', 'popular': True,
         'q': 'هل يجب أن أعرف البرمجة؟',
         'a': 'إطلاقاً لا. يتولى محرّرنا المباشر رفع الشعار وتغيير الألوان وتعديل النصوص واستبدال الصور دون سطر كود واحد. إذا أردت التعمق أكثر، فالكود المصدري الكامل ملك لك — نظيف وموثّق ومبني على معايير حديثة.'},
        {'cat': 'getting-started',
         'q': 'كم من الوقت يستغرق إطلاق موقعي؟',
         'a': 'ينتقل معظم العملاء من التصفح إلى موقع حي في أقل من 60 دقيقة. اختر قالباً، أضف محتواك عبر المحرّر، حمّل الحزمة، ارفعها على استضافتك. هذا هو سير العمل بأكمله.'},
        {'cat': 'getting-started',
         'q': 'ماذا يتضمن شراء القالب؟',
         'a': 'تتلقى حزمة الموقع الكاملة: HTML و CSS و JavaScript وخطوط وصور وجميع الموارد، بالإضافة إلى ترخيص تجاري لمشروع واحد. كما تحصل على 6 أشهر من التحديثات المجانية ودعم بريد إلكتروني ذو أولوية من فريقنا.'},

        {'cat': 'templates', 'popular': True,
         'q': 'هل يمكنني فعلاً تصفح كل صفحة قبل الشراء؟',
         'a': 'نعم. انقر معاينة على أي قالب ويمكنك تصفح الرئيسية ومن نحن والخدمات والتواصل والمعرض — كل صفحة تماماً كما يفعل زائر حقيقي. لا عروض مقفلة ولا لقطات مضلّلة. ما تراه هو ما تمتلكه.'},
        {'cat': 'templates',
         'q': 'كم عدد القوالب المتاحة؟',
         'a': 'يحتوي فهرسنا حالياً على أكثر من 190 قالباً فاخراً في 24 تصنيفاً، من العيادات البيطرية والمطاعم إلى SaaS والعقارات ومخططي الأعراس والاستوديوهات الإبداعية. تُضاف قوالب جديدة كل شهر.'},
        {'cat': 'templates',
         'q': 'هل القوالب متجاوبة وجاهزة للجوال؟',
         'a': 'كل قالب متجاوب بالكامل افتراضياً ومختبَر على شاشات سطح المكتب والجهاز اللوحي والجوال. يتيح لك محرّرنا أيضاً معاينة تعديلاتك في الأحجام الثلاثة قبل الشراء.'},
        {'cat': 'templates',
         'q': 'هل يمكنني استخدام قالب كنقطة بداية لمشروع عميل؟',
         'a': 'نعم — وهذا بالضبط ما يفعله كثير من مستخدمينا. ترخيص المشروع الواحد يغطي نطاق عميل واحد. لعملاء متعددين، تراخيصنا الموسَّعة واللامحدودة هي الخيار المناسب.'},

        {'cat': 'licensing', 'popular': True,
         'q': 'ماذا يغطي الترخيص القياسي؟',
         'a': 'ترخيص المشروع الواحد يسمح لك بنشر القالب على نطاق واحد لعمل واحد أو عميل واحد. يمكنك تعديل الكود بحرية، لكن لا يمكنك إعادة بيع القالب أو توزيعه. للوكالات والمستقلّين مع مشاريع متعددة، نقدم تراخيص موسَّعة ولا محدودة.'},
        {'cat': 'licensing',
         'q': 'ما تكلفة القالب؟',
         'a': 'تتراوح القوالب بين 39 و 89 يورو حسب التعقيد وعدد الصفحات. قوالب فئة النخبة ذات التفاعلات المتقدمة تبدأ من 79 يورو. كل سعر دفعة واحدة — بلا اشتراكات بلا رسوم مخفية بلا تجديد.'},
        {'cat': 'licensing',
         'q': 'هل تقدمون استرداد المبلغ؟',
         'a': 'نعم، كل عملية شراء محمية بسياسة استرداد مدتها 14 يوماً. إذا لم يلبِّ القالب توقعاتك لأي سبب، تواصل مع فريق الدعم وسنصلح الأمر — دون أسئلة.'},
        {'cat': 'licensing',
         'q': 'ما طرق الدفع المقبولة؟',
         'a': 'نقبل بطاقات الائتمان والخصم الرئيسية و PayPal و Apple Pay و Google Pay. تُعالَج جميع الدفعات عبر بوابات متوافقة مع PCI مع تشفير من طرف إلى طرف. يمكن لعملاء المؤسسات أيضاً الدفع عن طريق التحويل البنكي عند الطلب.'},

        {'cat': 'customization', 'popular': True,
         'q': 'ماذا يمكنني تخصيصه في المحرّر المباشر؟',
         'a': 'الشعار واسم العلامة والعنوان الترويجي والألوان الأساسية والثانوية وصورة ونص الهيرو والخدمات وصور الفريق وبيانات الاتصال وروابط التواصل وحقوق التذييل وغيرها. كل تعديل يُطبَّق فوراً في معاينة المتصفح.'},
        {'cat': 'customization',
         'q': 'هل سأتلقى تحديثات بعد الشراء؟',
         'a': 'نعم. كل قالب يتضمن 6 أشهر من التحديثات المجانية التي تشمل تصحيحات أمنية وإصلاحات توافق المتصفّحات وتحسينات طفيفة. ترقيات الإصدارات الكبرى مقدَّمة بسعر مخفّض للعملاء الحاليين.'},
        {'cat': 'customization',
         'q': 'ما نوع الدعم المتضمّن؟',
         'a': 'كل عملية شراء تتضمّن دعماً بالبريد الإلكتروني ذا أولوية مع زمن استجابة أقل من 24 ساعة في أيام العمل. لعملاء المؤسسات، نوفّر أيضاً مديري حسابات مخصّصين ومكالمات إعداد مباشرة.'},
        {'cat': 'customization',
         'q': 'هل يمكنني تغيير التصميم بعد التنزيل؟',
         'a': 'بالكامل. أنت تمتلك الكود المصدري الكامل — HTML و CSS و JavaScript وجميع الموارد. عدّل أو وسّع أو أعد بناء أي جزء من القالب ليناسب احتياجاتك بالضبط. توثيقنا يرشدك عبر كل قسم.'},

        {'cat': 'enterprise',
         'q': 'هل تقدّمون خصومات على الحجم للوكالات؟',
         'a': 'نعم. تراخيصنا الموسَّعة واللامحدودة مصمّمة خصيصاً للوكالات والمستقلّين الذين يبنون مواقع لعملاء متعدّدين. تواصل مع فريق المؤسسات للحصول على تسعير مخصّص بناءً على حجمك.'},
        {'cat': 'enterprise',
         'q': 'هل يمكن لفريقي التعاون على التخصيص نفسه؟',
         'a': 'تتضمّن خطط المؤسسات مساحات عمل مشتركة حيث يمكن لفريقك التعليق والمراجعة واعتماد التخصيصات معاً قبل تصدير الحزمة النهائية. نوفّر أيضاً تحكماً بالوصول قائماً على الأدوار.'},
        {'cat': 'enterprise',
         'q': 'هل بدرواي مناسب للنشر على نطاق واسع؟',
         'a': 'بالتأكيد. منصتنا مبنية على Django — نفس الحزمة التي يثق بها إنستغرام وسبوتيفاي وبنترست — وجاهزة لاتفاقيات مستوى الخدمة للمؤسسات. تواصل معنا لمناقشة الاستضافة المخصّصة والتراخيص المخصّصة وخيارات العلامة البيضاء.'},
    ],
}


def get_categorized_faqs(locale='en'):
    """Return (categories, faqs) for the locale.

    Categories is a list of (key, label, icon).
    Faqs is the full list with `cat`, `q`, `a`, optional `popular`.
    """
    cats = FAQ_CATEGORIES.get(locale, FAQ_CATEGORIES['en'])
    faqs = FAQ_CATEGORIZED.get(locale, FAQ_CATEGORIZED['en'])
    return cats, faqs


# ================================================================
# LOCALIZED TESTIMONIALS / REVIEWS POOL
# ================================================================
TESTIMONIAL_POOL = {
    'en': [
        {'name': 'Sarah Johnson', 'role': 'Founder, PawCentral Veterinary',
         'rating': 5, 'avatar': 'https://i.pravatar.cc/120?img=47',
         'text': 'I launched my clinic website in two hours. The customizer let me drop in our logo, photos and services while I watched the site come to life. My patients love it.'},
        {'name': 'Marcus Chen', 'role': 'Creative Director, Studio Nine',
         'rating': 5, 'avatar': 'https://i.pravatar.cc/120?img=12',
         'text': 'As an agency we use Sitegency for rapid client prototyping. The quality is genuinely premium — not the usual template marketplace junk. Our clients cannot believe we did not build from scratch.'},
        {'name': 'Elena Rodriguez', 'role': 'Owner, Bistro Saveur',
         'rating': 5, 'avatar': 'https://i.pravatar.cc/120?img=32',
         'text': 'Before Sitegency I was quoted 8,000 euros by three agencies. I spent 79 euros here, previewed the exact site before buying, and launched the same day. The template is stunning.'},
    ],
    'it': [
        {'name': 'Sara Bianchi', 'role': 'Fondatrice, Clinica Veterinaria Pet Central',
         'rating': 5, 'avatar': 'https://i.pravatar.cc/120?img=47',
         'text': 'Ho lanciato il sito della mia clinica in due ore. Il customizer mi ha permesso di inserire logo, foto e servizi mentre guardavo il sito prendere vita. I miei pazienti lo adorano.'},
        {'name': 'Marco Conti', 'role': 'Direttore creativo, Studio Nove',
         'rating': 5, 'avatar': 'https://i.pravatar.cc/120?img=12',
         'text': 'Come agenzia usiamo Sitegency per prototipi rapidi. La qualità è veramente premium — non la solita spazzatura dei marketplace di template. I nostri clienti non credono che non lo abbiamo costruito da zero.'},
        {'name': 'Elena Rossi', 'role': 'Titolare, Bistrot Saveur',
         'rating': 5, 'avatar': 'https://i.pravatar.cc/120?img=32',
         'text': 'Prima di Sitegency mi avevano chiesto 8.000 euro da tre agenzie diverse. Ho speso 79 euro qui, ho visto l esatto sito prima di comprarlo e l ho lanciato lo stesso giorno. Il template è stupendo.'},
    ],
    'fr': [
        {'name': 'Sophie Martin', 'role': 'Fondatrice, Clinique Vétérinaire PatteCentral',
         'rating': 5, 'avatar': 'https://i.pravatar.cc/120?img=47',
         'text': 'J ai lancé le site de ma clinique en deux heures. L éditeur m a permis d ajouter notre logo, nos photos et nos services pendant que je regardais le site prendre vie. Mes patients l adorent.'},
        {'name': 'Marc Dubois', 'role': 'Directeur créatif, Studio Neuf',
         'rating': 5, 'avatar': 'https://i.pravatar.cc/120?img=12',
         'text': 'En tant qu agence nous utilisons Sitegency pour du prototypage rapide. La qualité est vraiment premium — pas la camelote habituelle des marketplaces. Nos clients ne peuvent pas croire que nous n avons pas construit depuis zéro.'},
        {'name': 'Elena Laurent', 'role': 'Propriétaire, Bistrot Saveur',
         'rating': 5, 'avatar': 'https://i.pravatar.cc/120?img=32',
         'text': 'Avant Sitegency on m avait proposé 8 000 euros par trois agences. J ai dépensé 79 euros ici, j ai vu le site exact avant de l acheter, et je l ai lancé le jour même. Le template est magnifique.'},
    ],
    'ar': [
        {'name': 'سارة العلي', 'role': 'مؤسِّسة، عيادة باوسنترال البيطرية',
         'rating': 5, 'avatar': 'https://i.pravatar.cc/120?img=47',
         'text': 'أطلقت موقع عيادتي في ساعتين. سمح لي المحرّر بإضافة شعارنا وصورنا وخدماتنا بينما أشاهد الموقع يتشكّل أمامي. يحبّه مرضاي كثيراً.'},
        {'name': 'مارك كريم', 'role': 'المدير الإبداعي، استوديو ناين',
         'rating': 5, 'avatar': 'https://i.pravatar.cc/120?img=12',
         'text': 'كوكالة، نستخدم بدرواي لإنجاز النماذج الأولية بسرعة. الجودة فاخرة حقاً — ليست السخافة المعتادة في أسواق القوالب. عملاؤنا لا يصدّقون أننا لم نبنِ كل شيء من الصفر.'},
        {'name': 'إيلينا منصور', 'role': 'صاحبة، بيسترو ساڨور',
         'rating': 5, 'avatar': 'https://i.pravatar.cc/120?img=32',
         'text': 'قبل بدرواي، عرضت عليّ ثلاث وكالات مبالغ 8000 يورو. دفعت هنا 79 يورو فقط، عاينت الموقع بالضبط قبل الشراء، وأطلقته في نفس اليوم. القالب رائع.'},
    ],
}


def get_localized_testimonials(locale='en'):
    """Return 3 locale-native testimonials."""
    return TESTIMONIAL_POOL.get(locale, TESTIMONIAL_POOL['en'])


# ================================================================
# CATEGORY TAGLINES & DESCRIPTIONS — locale-native
# ================================================================
CATEGORY_CONTENT = {
    # key: category.slug → { locale: { tagline, description } }
    'animal': {
        'en': {
            'tagline': 'Websites that speak for the voiceless',
            'description': 'Warm, trustworthy templates crafted for veterinary clinics, pet stores, animal shelters and pet-care businesses. Every page designed to inspire confidence and compassion — from adoption stories to emergency contact forms.',
        },
        'it': {
            'tagline': 'Siti che parlano per chi non ha voce',
            'description': 'Template caldi e affidabili pensati per cliniche veterinarie, pet shop, rifugi e attività legate al mondo animale. Ogni pagina è progettata per ispirare fiducia e compassione — dalle storie di adozione ai moduli di contatto d\'emergenza.',
        },
        'fr': {
            'tagline': 'Des sites qui parlent pour ceux qui ne peuvent pas',
            'description': 'Des templates chaleureux et rassurants pensés pour les cliniques vétérinaires, animaleries, refuges et professionnels du monde animal. Chaque page est conçue pour inspirer confiance et compassion — des histoires d\'adoption aux formulaires d\'urgence.',
        },
        'ar': {
            'tagline': 'مواقع تتحدث باسم من لا صوت لهم',
            'description': 'قوالب دافئة وموثوقة صُنعت للعيادات البيطرية ومحلات الحيوانات الأليفة والملاجئ وكل من يعمل في رعاية الحيوان. كل صفحة مُصمَّمة لتبعث الثقة والرحمة — من قصص التبني إلى نماذج التواصل في الحالات الطارئة.',
        },
    },
    'medical': {
        'en': {
            'tagline': 'Healthcare-grade design, ready out of the box',
            'description': 'Clean, reassuring templates for hospitals, clinics, dentists and wellness specialists. Calm palettes, accessible typography and appointment-first layouts designed to build patient trust from the very first scroll.',
        },
        'it': {
            'tagline': 'Design di livello sanitario, pronto all\'uso',
            'description': 'Template puliti e rassicuranti per ospedali, cliniche, dentisti e professionisti del benessere. Palette calme, tipografia accessibile e layout orientati alla prenotazione, pensati per costruire la fiducia del paziente dal primo scroll.',
        },
        'fr': {
            'tagline': 'Design médical professionnel, prêt à l\'emploi',
            'description': 'Des templates nets et rassurants pour hôpitaux, cliniques, dentistes et professionnels du bien-être. Palettes apaisantes, typographie accessible et mises en page centrées sur la prise de rendez-vous, conçues pour inspirer confiance dès le premier coup d\'œil.',
        },
        'ar': {
            'tagline': 'تصميم طبي احترافي، جاهز فوراً',
            'description': 'قوالب نظيفة ومطمئنة للمستشفيات والعيادات وأطباء الأسنان والمتخصصين في العافية. ألوان هادئة وخطوط سهلة القراءة وتخطيطات تركّز على الحجز، مُصمَّمة لبناء ثقة المريض منذ اللحظة الأولى.',
        },
    },
    'restaurant': {
        'en': {
            'tagline': 'Serve your brand before the first course',
            'description': 'Appetizing templates for restaurants, cafés, bakeries, food trucks and gourmet experiences. Every layout showcases the menu, the atmosphere and the story behind your kitchen with the elegance your cuisine deserves.',
        },
        'it': {
            'tagline': 'Servi il tuo brand prima ancora della prima portata',
            'description': 'Template appetitosi per ristoranti, caffè, panetterie, food truck e esperienze gourmet. Ogni layout mette in mostra il menu, l\'atmosfera e la storia dietro la tua cucina con l\'eleganza che i tuoi piatti meritano.',
        },
        'fr': {
            'tagline': 'Servez votre marque avant l\'entrée',
            'description': 'Des templates appétissants pour restaurants, cafés, boulangeries, food trucks et expériences gastronomiques. Chaque mise en page met en valeur le menu, l\'ambiance et l\'histoire derrière votre cuisine avec toute l\'élégance qu\'elle mérite.',
        },
        'ar': {
            'tagline': 'قدّم علامتك قبل الطبق الأول',
            'description': 'قوالب شهية للمطاعم والمقاهي والمخابز ومطابخ الطعام المتنقلة وتجارب الذواقة. كل تخطيط يُبرز القائمة والأجواء وقصة مطبخك بالأناقة التي يستحقها طعامك.',
        },
    },
    'hotel': {
        'en': {
            'tagline': 'Luxury hospitality, elegantly presented online',
            'description': 'Premium templates for hotels, resorts, bed & breakfasts and hospitality brands. Cinematic hero layouts, elegant room galleries and friction-free booking flows create digital experiences that match your in-person luxury.',
        },
        'it': {
            'tagline': 'Ospitalità di lusso, presentata online con eleganza',
            'description': 'Template premium per hotel, resort, bed & breakfast e brand dell\'ospitalità. Hero cinematografiche, gallerie camere eleganti e flussi di prenotazione senza attriti creano esperienze digitali all\'altezza del lusso vissuto in presenza.',
        },
        'fr': {
            'tagline': 'L\'hospitalité de luxe, présentée en ligne avec élégance',
            'description': 'Des templates premium pour hôtels, resorts, chambres d\'hôtes et marques hospitalières. Des hero cinématographiques, des galeries de chambres élégantes et des parcours de réservation sans friction créent des expériences digitales à la hauteur de votre luxe physique.',
        },
        'ar': {
            'tagline': 'ضيافة فاخرة تُقدَّم إلكترونياً بأناقة',
            'description': 'قوالب فاخرة للفنادق والمنتجعات وبيوت الضيافة وعلامات الضيافة. صور رئيسية سينمائية ومعارض غرف أنيقة وعمليات حجز سلسة تخلق تجربة رقمية بمستوى فخامة الواقع.',
        },
    },
    'beauty': {
        'en': {
            'tagline': 'Elegant digital presence for beauty professionals',
            'description': 'Refined templates for salons, spas, makeup artists and wellness studios. Every page is a mirror of your craft — elegant typography, signature imagery and booking forms that turn visitors into regulars.',
        },
        'it': {
            'tagline': 'Presenza digitale elegante per professionisti del beauty',
            'description': 'Template raffinati per saloni, spa, make-up artist e studi wellness. Ogni pagina è uno specchio del tuo mestiere — tipografia elegante, immagini distintive e moduli di prenotazione che trasformano i visitatori in clienti fedeli.',
        },
        'fr': {
            'tagline': 'Une présence digitale élégante pour les professionnels de la beauté',
            'description': 'Des templates raffinés pour salons, spas, maquilleurs et studios de bien-être. Chaque page reflète votre art — typographie élégante, imagerie signature et formulaires de réservation qui transforment les visiteurs en clients fidèles.',
        },
        'ar': {
            'tagline': 'حضور رقمي أنيق لمحترفي التجميل',
            'description': 'قوالب راقية للصالونات والسبا وفنانات المكياج واستوديوهات العافية. كل صفحة مرآة لفنّك — خطوط أنيقة وصور مميزة ونماذج حجز تحوّل الزائرين إلى عملاء دائمين.',
        },
    },
    'barber': {
        'en': {
            'tagline': 'Sharp templates for modern barbershops',
            'description': 'Bold, masculine templates tailored to barbershops and men\'s grooming studios. Confident typography, grit-and-chrome aesthetics and booking-first architecture turn every visit into a ritual.',
        },
        'it': {
            'tagline': 'Template taglienti per barbershop moderni',
            'description': 'Template decisi e maschili pensati per barbershop e studi di grooming maschile. Tipografia sicura, estetica grit-and-chrome e architettura booking-first trasformano ogni visita in un rituale.',
        },
        'fr': {
            'tagline': 'Des templates tranchants pour barbershops modernes',
            'description': 'Des templates audacieux et masculins conçus pour les barbershops et studios de soin masculin. Typographie affirmée, esthétique métal-cuir et architecture centrée sur la réservation transforment chaque visite en rituel.',
        },
        'ar': {
            'tagline': 'قوالب حادة لصالونات الحلاقة الحديثة',
            'description': 'قوالب جريئة ومميزة صُنعت لصالونات الحلاقة واستوديوهات العناية بالرجال. خطوط واثقة وجماليات صلبة ونظام حجز مباشر يحوّلون كل زيارة إلى طقس.',
        },
    },
    'fitness': {
        'en': {
            'tagline': 'Websites as powerful as your workouts',
            'description': 'High-energy templates for gyms, personal trainers, yoga studios and wellness centers. Dynamic imagery, motivational typography and class-scheduling flows designed to convert curious visitors into committed members.',
        },
        'it': {
            'tagline': 'Siti potenti come i tuoi allenamenti',
            'description': 'Template ad alta energia per palestre, personal trainer, studi yoga e centri benessere. Immagini dinamiche, tipografia motivazionale e flussi di prenotazione corsi pensati per trasformare curiosi in iscritti convinti.',
        },
        'fr': {
            'tagline': 'Des sites aussi puissants que vos séances',
            'description': 'Des templates énergiques pour salles de sport, coachs, studios de yoga et centres de bien-être. Imagerie dynamique, typographie motivante et parcours de réservation de cours conçus pour transformer les curieux en membres engagés.',
        },
        'ar': {
            'tagline': 'مواقع بقوة تمارينك',
            'description': 'قوالب مفعمة بالطاقة للصالات الرياضية والمدربين الشخصيين واستوديوهات اليوغا ومراكز العافية. صور ديناميكية وخطوط محفِّزة ونظام حجز الحصص مصمّم لتحويل الفضوليين إلى أعضاء ملتزمين.',
        },
    },
    'real-estate': {
        'en': {
            'tagline': 'Open the door to premium real estate websites',
            'description': 'Sophisticated templates for agencies, brokers, property listings and luxury real estate. Cinematic listing galleries, smart filters and inquiry flows that turn browsers into buyers.',
        },
        'it': {
            'tagline': 'Apri la porta a siti immobiliari premium',
            'description': 'Template sofisticati per agenzie, mediatori, annunci immobiliari e immobili di lusso. Gallerie cinematografiche, filtri intelligenti e flussi di contatto che trasformano i visitatori in acquirenti.',
        },
        'fr': {
            'tagline': 'Ouvrez la porte à des sites immobiliers premium',
            'description': 'Des templates sophistiqués pour agences, courtiers, annonces et biens de luxe. Galeries cinématographiques, filtres intelligents et parcours de contact qui transforment les visiteurs en acheteurs.',
        },
        'ar': {
            'tagline': 'افتح الباب لمواقع عقارية فاخرة',
            'description': 'قوالب راقية للوكالات والوسطاء وعروض العقارات والعقارات الفاخرة. معارض سينمائية وفلاتر ذكية وقنوات تواصل تحوّل المتصفحين إلى مشترين.',
        },
    },
    'education': {
        'en': {
            'tagline': 'Educational platforms that inspire learning',
            'description': 'Modern templates for schools, universities, online courses and learning platforms. Structured course catalogs, student stories and enrollment flows designed around one goal — making knowledge irresistible.',
        },
        'it': {
            'tagline': 'Piattaforme educative che ispirano l\'apprendimento',
            'description': 'Template moderni per scuole, università, corsi online e piattaforme di learning. Cataloghi strutturati, storie di studenti e flussi di iscrizione progettati attorno a un obiettivo: rendere la conoscenza irresistibile.',
        },
        'fr': {
            'tagline': 'Des plateformes éducatives qui inspirent l\'apprentissage',
            'description': 'Des templates modernes pour écoles, universités, cours en ligne et plateformes d\'apprentissage. Catalogues structurés, histoires d\'étudiants et parcours d\'inscription conçus autour d\'un objectif — rendre le savoir irrésistible.',
        },
        'ar': {
            'tagline': 'منصات تعليمية تُلهم حب التعلم',
            'description': 'قوالب حديثة للمدارس والجامعات والدورات الإلكترونية ومنصات التعلم. فهارس مرتبة وقصص طلاب وعمليات تسجيل مصمّمة حول هدف واحد — جعل المعرفة لا تُقاوَم.',
        },
    },
    'agency': {
        'en': {
            'tagline': 'Agency-grade templates for creative studios',
            'description': 'Bold and creative templates for digital agencies, studios and creative professionals. Case-study layouts, portfolio showcases and lead-capture flows designed to win the pitch before the first meeting.',
        },
        'it': {
            'tagline': 'Template da agenzia per studi creativi',
            'description': 'Template audaci e creativi per agenzie digitali, studi e professionisti creativi. Layout dedicati ai case study, showcase di portfolio e flussi di contatto progettati per vincere il pitch prima ancora del primo incontro.',
        },
        'fr': {
            'tagline': 'Des templates d\'agence pour studios créatifs',
            'description': 'Des templates audacieux et créatifs pour agences digitales, studios et professionnels de la création. Mises en page d\'études de cas, vitrines de portfolio et parcours de contact conçus pour gagner le pitch avant même la première réunion.',
        },
        'ar': {
            'tagline': 'قوالب بمستوى الوكالات للاستوديوهات الإبداعية',
            'description': 'قوالب جريئة وإبداعية للوكالات الرقمية والاستوديوهات والمبدعين. تخطيطات لدراسات الحالة ومعارض الأعمال وقنوات تواصل مصمّمة لكسب العقد قبل الاجتماع الأول.',
        },
    },
    'technology': {
        'en': {
            'tagline': 'The future of tech websites, today',
            'description': 'Innovation-driven templates for SaaS, startups, software houses and tech brands. Feature explainers, pricing tiers and product demos optimized to turn trials into paying customers.',
        },
        'it': {
            'tagline': 'Il futuro dei siti tech, oggi',
            'description': 'Template guidati dall\'innovazione per SaaS, startup, software house e brand tech. Pagine feature, piani tariffari e demo di prodotto ottimizzate per trasformare le prove gratuite in clienti paganti.',
        },
        'fr': {
            'tagline': 'Le futur des sites tech, aujourd\'hui',
            'description': 'Des templates innovants pour SaaS, startups, éditeurs de logiciels et marques tech. Pages de fonctionnalités, grilles tarifaires et démos produit optimisées pour convertir les essais en clients payants.',
        },
        'ar': {
            'tagline': 'مستقبل مواقع التقنية، اليوم',
            'description': 'قوالب تعتمد على الابتكار لشركات SaaS والشركات الناشئة وشركات البرمجيات والعلامات التقنية. صفحات المزايا وخطط التسعير والعروض التوضيحية مُحسَّنة لتحويل التجارب إلى عملاء مدفوعين.',
        },
    },
    'lawyer': {
        'en': {
            'tagline': 'Authority, trust, and precision in every pixel',
            'description': 'Professional templates for law firms, attorneys and legal consultants. Crisp layouts, practice-area pages and consultation request flows designed to communicate authority and inspire the trust your cases deserve.',
        },
        'it': {
            'tagline': 'Autorevolezza, fiducia e precisione in ogni pixel',
            'description': 'Template professionali per studi legali, avvocati e consulenti giuridici. Layout nitidi, pagine di aree di attività e flussi di richiesta consulenza progettati per comunicare autorevolezza e ispirare la fiducia che i tuoi casi meritano.',
        },
        'fr': {
            'tagline': 'Autorité, confiance et précision dans chaque pixel',
            'description': 'Des templates professionnels pour cabinets d\'avocats et conseillers juridiques. Mises en page précises, pages de domaines d\'expertise et parcours de prise de rendez-vous conçus pour communiquer l\'autorité et inspirer la confiance que vos dossiers méritent.',
        },
        'ar': {
            'tagline': 'سلطة وثقة ودقة في كل بكسل',
            'description': 'قوالب احترافية لمكاتب المحاماة والمحامين والمستشارين القانونيين. تخطيطات دقيقة وصفحات مجالات الممارسة وقنوات طلب الاستشارة مصمّمة لتوصيل السلطة وإلهام الثقة التي تستحقها قضاياك.',
        },
    },
    'construction': {
        'en': {
            'tagline': 'Build your digital presence with solid foundations',
            'description': 'Industrial templates for construction companies, contractors and builders. Project galleries, service pages and quote request flows designed to demonstrate the craftsmanship that earns trust.',
        },
        'it': {
            'tagline': 'Costruisci la tua presenza digitale su fondamenta solide',
            'description': 'Template industriali per imprese edili, appaltatori e costruttori. Gallerie progetti, pagine servizi e flussi di richiesta preventivo progettati per dimostrare l\'artigianalità che conquista la fiducia.',
        },
        'fr': {
            'tagline': 'Bâtissez votre présence digitale sur des fondations solides',
            'description': 'Des templates industriels pour entreprises du bâtiment, entrepreneurs et constructeurs. Galeries de projets, pages services et parcours de demande de devis conçus pour démontrer le savoir-faire qui gagne la confiance.',
        },
        'ar': {
            'tagline': 'ابنِ حضورك الرقمي على أسس صلبة',
            'description': 'قوالب صناعية لشركات البناء والمقاولين. معارض المشاريع وصفحات الخدمات وقنوات طلب عروض الأسعار مصمّمة لتُظهر الحرفية التي تكسب الثقة.',
        },
    },
    'architects': {
        'en': {
            'tagline': 'Blueprints for award-winning studios',
            'description': 'Minimalist templates for architecture studios and interior designers. Project galleries, studio stories and inquiry flows crafted to let your work speak first — with the restraint that lets every line breathe.',
        },
        'it': {
            'tagline': 'Progetti per studi da premio',
            'description': 'Template minimalisti per studi di architettura e interior designer. Gallerie progetti, storie di studio e flussi di contatto pensati per lasciare parlare il tuo lavoro — con la sobrietà che fa respirare ogni linea.',
        },
        'fr': {
            'tagline': 'Des plans pour studios primés',
            'description': 'Des templates minimalistes pour studios d\'architecture et designers d\'intérieur. Galeries de projets, récits de studio et parcours de contact conçus pour laisser parler votre travail — avec la sobriété qui fait respirer chaque ligne.',
        },
        'ar': {
            'tagline': 'مخططات لاستوديوهات حائزة على جوائز',
            'description': 'قوالب بسيطة لاستوديوهات العمارة ومصممي الديكور. معارض مشاريع وقصص استوديو وقنوات تواصل صُنعت لترك عملك يتحدث أولاً — ببساطة تُتيح لكل خط أن يتنفس.',
        },
    },
    'automotive': {
        'en': {
            'tagline': 'High-performance websites for the auto industry',
            'description': 'Sleek templates for car dealerships, auto repair shops and automotive brands. Vehicle galleries, service pages and booking flows engineered to convert browsers into owners.',
        },
        'it': {
            'tagline': 'Siti ad alte prestazioni per l\'industria automotive',
            'description': 'Template eleganti per concessionarie, officine e brand automotive. Gallerie veicoli, pagine servizi e flussi di prenotazione progettati per trasformare i visitatori in proprietari.',
        },
        'fr': {
            'tagline': 'Des sites hautes performances pour l\'industrie automobile',
            'description': 'Des templates élégants pour concessionnaires, garages et marques automobiles. Galeries de véhicules, pages services et parcours de réservation conçus pour transformer les visiteurs en propriétaires.',
        },
        'ar': {
            'tagline': 'مواقع بأداء عالٍ لقطاع السيارات',
            'description': 'قوالب أنيقة لوكالات السيارات وورش الإصلاح وعلامات السيارات. معارض مركبات وصفحات خدمات وأنظمة حجز مُصمَّمة لتحويل المتصفحين إلى مُلاك.',
        },
    },
    'wedding': {
        'en': {
            'tagline': 'Celebrate love with unforgettable websites',
            'description': 'Romantic templates for wedding planners, venues and engagement events. Story-driven layouts, gallery showcases and RSVP flows that turn every visit into anticipation of the big day.',
        },
        'it': {
            'tagline': 'Celebra l\'amore con siti indimenticabili',
            'description': 'Template romantici per wedding planner, location ed eventi di fidanzamento. Layout narrativi, gallerie e flussi RSVP che trasformano ogni visita in attesa del grande giorno.',
        },
        'fr': {
            'tagline': 'Célébrez l\'amour avec des sites inoubliables',
            'description': 'Des templates romantiques pour wedding planners, lieux de réception et événements de fiançailles. Mises en page narratives, galeries et parcours RSVP qui transforment chaque visite en anticipation du grand jour.',
        },
        'ar': {
            'tagline': 'احتفلوا بالحب بمواقع لا تُنسى',
            'description': 'قوالب رومانسية لمنظّمي الأعراس وقاعات الاحتفالات ومناسبات الخطوبة. تخطيطات قصصية ومعارض وأنظمة تأكيد حضور تحوّل كل زيارة إلى ترقّب اليوم الكبير.',
        },
    },
    'portfolio': {
        'en': {
            'tagline': 'Showcase your work like the professional you are',
            'description': 'Minimal portfolio templates for creatives, freelancers and personal brands. Typography-led layouts, project case studies and contact flows engineered to turn viewers into clients.',
        },
        'it': {
            'tagline': 'Mostra il tuo lavoro come il professionista che sei',
            'description': 'Template portfolio minimal per creativi, freelance e personal brand. Layout guidati dalla tipografia, case study di progetti e flussi di contatto progettati per trasformare i visitatori in clienti.',
        },
        'fr': {
            'tagline': 'Présentez votre travail comme le professionnel que vous êtes',
            'description': 'Des templates de portfolio minimalistes pour créatifs, freelances et marques personnelles. Mises en page typographiques, études de cas de projets et parcours de contact conçus pour transformer les visiteurs en clients.',
        },
        'ar': {
            'tagline': 'اعرض أعمالك كما يليق بمحترف',
            'description': 'قوالب محفظة أعمال بسيطة للمبدعين والمستقلين والعلامات الشخصية. تخطيطات تعتمد على الخطوط ودراسات حالة للمشاريع وقنوات تواصل مصمّمة لتحويل المشاهدين إلى عملاء.',
        },
    },
    'business': {
        'en': {
            'tagline': 'Corporate elegance, startup energy',
            'description': 'Versatile business templates for corporations, consultancies and enterprise brands. Value-prop layouts, case studies and contact flows built for credibility at every scale.',
        },
        'it': {
            'tagline': 'Eleganza corporate, energia da startup',
            'description': 'Template business versatili per aziende, società di consulenza e brand enterprise. Layout di value proposition, case study e flussi di contatto pensati per la credibilità a ogni scala.',
        },
        'fr': {
            'tagline': 'Élégance corporate, énergie startup',
            'description': 'Des templates business polyvalents pour entreprises, cabinets de conseil et marques enterprise. Mises en page de proposition de valeur, études de cas et parcours de contact conçus pour la crédibilité à toutes les échelles.',
        },
        'ar': {
            'tagline': 'أناقة مؤسسية وطاقة شركات ناشئة',
            'description': 'قوالب أعمال متعددة الاستخدامات للشركات وشركات الاستشارات والعلامات المؤسسية. تخطيطات لعرض القيمة ودراسات حالة وقنوات تواصل مصمّمة للمصداقية على أي نطاق.',
        },
    },
    'e-commerce': {
        'en': {
            'tagline': 'Sell more with conversion-ready storefronts',
            'description': 'High-converting templates for online stores, fashion boutiques and digital shops. Product grids, checkout flows and cart experiences optimized to turn clicks into customers.',
        },
        'it': {
            'tagline': 'Vendi di più con vetrine pronte alla conversione',
            'description': 'Template ad alta conversione per negozi online, boutique di moda e shop digitali. Griglie prodotto, flussi di checkout ed esperienze carrello ottimizzate per trasformare i click in clienti.',
        },
        'fr': {
            'tagline': 'Vendez plus avec des vitrines prêtes à convertir',
            'description': 'Des templates à fort taux de conversion pour boutiques en ligne, boutiques de mode et shops digitaux. Grilles produit, parcours de paiement et expériences panier optimisés pour transformer les clics en clients.',
        },
        'ar': {
            'tagline': 'بِع أكثر بواجهات جاهزة للتحويل',
            'description': 'قوالب عالية التحويل للمتاجر الإلكترونية وبوتيكات الموضة والمتاجر الرقمية. شبكات منتجات ورحلات شراء وتجارب سلة مُحسَّنة لتحويل النقرات إلى عملاء.',
        },
    },
    'finance': {
        'en': {
            'tagline': 'Financial services websites built on trust',
            'description': 'Professional templates for banks, fintech startups and investment firms. Transparent pricing tables, secure contact flows and compliance-aware layouts that earn trust from the first impression.',
        },
        'it': {
            'tagline': 'Siti di servizi finanziari costruiti sulla fiducia',
            'description': 'Template professionali per banche, fintech e società di investimento. Tabelle prezzi trasparenti, flussi di contatto sicuri e layout orientati alla compliance che conquistano la fiducia dalla prima impressione.',
        },
        'fr': {
            'tagline': 'Des sites de services financiers bâtis sur la confiance',
            'description': 'Des templates professionnels pour banques, fintechs et sociétés d\'investissement. Tableaux de tarifs transparents, parcours de contact sécurisés et mises en page respectant la conformité qui gagnent la confiance dès la première impression.',
        },
        'ar': {
            'tagline': 'مواقع خدمات مالية مبنية على الثقة',
            'description': 'قوالب احترافية للبنوك وشركات التقنية المالية الناشئة ومؤسسات الاستثمار. جداول أسعار شفافة وقنوات تواصل آمنة وتخطيطات تراعي الامتثال تكسب الثقة من الانطباع الأول.',
        },
    },
    'fashion': {
        'en': {
            'tagline': 'Runway-ready websites for fashion brands',
            'description': 'Editorial templates for fashion designers, boutiques, stylists and models. Lookbook galleries, campaign layouts and shoppable experiences designed to feel straight from the front row.',
        },
        'it': {
            'tagline': 'Siti pronti per la passerella per brand di moda',
            'description': 'Template editoriali per stilisti, boutique, stylist e modelli. Gallerie lookbook, layout campagne ed esperienze shoppable pensate per trasmettere la sensazione della prima fila alle sfilate.',
        },
        'fr': {
            'tagline': 'Des sites prêts pour le podium pour marques de mode',
            'description': 'Des templates éditoriaux pour créateurs, boutiques, stylistes et mannequins. Galeries lookbook, mises en page de campagnes et expériences shoppables conçues pour évoquer la sensation du front row.',
        },
        'ar': {
            'tagline': 'مواقع بمستوى منصات الموضة للعلامات',
            'description': 'قوالب تحريرية لمصممي الأزياء والبوتيكات والمصوّرين والعارضات. معارض لوك بوك وتخطيطات حملات وتجارب تسوّق مُصمَّمة لتنقل إحساس الصف الأمامي في عروض الأزياء.',
        },
    },
    'blog': {
        'en': {
            'tagline': 'Publishing platforms that readers love',
            'description': 'Editorial templates for blogs, magazines, news sites and personal publications. Typography-first layouts, reading flows and subscription mechanics that turn readers into regulars.',
        },
        'it': {
            'tagline': 'Piattaforme editoriali che i lettori amano',
            'description': 'Template editoriali per blog, magazine, siti di notizie e pubblicazioni personali. Layout typography-first, flussi di lettura e meccaniche di iscrizione che trasformano i lettori in habitué.',
        },
        'fr': {
            'tagline': 'Des plateformes éditoriales que les lecteurs adorent',
            'description': 'Des templates éditoriaux pour blogs, magazines, sites d\'actualités et publications personnelles. Mises en page typographiques, parcours de lecture et mécaniques d\'abonnement qui transforment les lecteurs en habitués.',
        },
        'ar': {
            'tagline': 'منصات نشر يعشقها القراء',
            'description': 'قوالب تحريرية للمدونات والمجلات ومواقع الأخبار والمنشورات الشخصية. تخطيطات تعتمد على الخط أولاً ومسارات قراءة وآليات اشتراك تحوّل القارئ إلى زائر منتظم.',
        },
    },
    'charity': {
        'en': {
            'tagline': 'Websites that move people to act',
            'description': 'Heartfelt templates for non-profits, charities and community initiatives. Cause storytelling, donation flows and volunteer sign-ups designed to turn empathy into action.',
        },
        'it': {
            'tagline': 'Siti che spingono le persone ad agire',
            'description': 'Template sinceri per non-profit, enti benefici e iniziative comunitarie. Storytelling di causa, flussi di donazione e iscrizione volontari progettati per trasformare l\'empatia in azione.',
        },
        'fr': {
            'tagline': 'Des sites qui poussent les gens à agir',
            'description': 'Des templates sincères pour associations, œuvres de charité et initiatives communautaires. Storytelling engagé, parcours de don et inscription de bénévoles conçus pour transformer l\'empathie en action.',
        },
        'ar': {
            'tagline': 'مواقع تدفع الناس للفعل',
            'description': 'قوالب صادقة للمنظمات غير الربحية والجمعيات الخيرية والمبادرات المجتمعية. سرد قضايا وقنوات تبرع وتسجيل متطوعين مصمّمة لتحويل التعاطف إلى فعل.',
        },
    },
    'app-landing': {
        'en': {
            'tagline': 'Launch your app with a killer first impression',
            'description': 'Conversion-optimized landing templates for mobile apps, SaaS products and launches. Feature highlights, social proof and store-download flows designed to maximize install rates.',
        },
        'it': {
            'tagline': 'Lancia la tua app con una prima impressione devastante',
            'description': 'Template landing ottimizzati per la conversione, per app mobile, prodotti SaaS e lanci. Feature highlight, social proof e flussi verso gli store progettati per massimizzare i tassi di installazione.',
        },
        'fr': {
            'tagline': 'Lancez votre app avec une première impression époustouflante',
            'description': 'Des templates de landing optimisés pour la conversion, pour apps mobiles, produits SaaS et lancements. Mise en avant de fonctionnalités, preuves sociales et parcours vers les stores conçus pour maximiser les installations.',
        },
        'ar': {
            'tagline': 'أطلق تطبيقك بانطباع أول مذهل',
            'description': 'قوالب landing مُحسَّنة للتحويل، للتطبيقات المحمولة ومنتجات SaaS وعمليات الإطلاق. إبراز المزايا وإثبات اجتماعي ومسارات إلى المتاجر مصمّمة لتعظيم معدلات التثبيت.',
        },
    },
    'creative': {
        'en': {
            'tagline': 'For brands that refuse to be boring',
            'description': 'Unconventional templates for creative studios, artists and visionary brands. Experimental layouts, bold typography and kinetic interactions designed for work that deserves to be noticed.',
        },
        'it': {
            'tagline': 'Per brand che rifiutano di essere banali',
            'description': 'Template non convenzionali per studi creativi, artisti e brand visionari. Layout sperimentali, tipografia decisa e interazioni cinetiche pensate per un lavoro che merita di essere notato.',
        },
        'fr': {
            'tagline': 'Pour les marques qui refusent d\'être banales',
            'description': 'Des templates non conventionnels pour studios créatifs, artistes et marques visionnaires. Mises en page expérimentales, typographie audacieuse et interactions cinétiques conçues pour un travail qui mérite d\'être remarqué.',
        },
        'ar': {
            'tagline': 'للعلامات التي ترفض أن تكون عادية',
            'description': 'قوالب غير تقليدية للاستوديوهات الإبداعية والفنانين والعلامات ذات الرؤية. تخطيطات تجريبية وخطوط جريئة وتفاعلات حركية مصمّمة لعمل يستحق أن يُرى.',
        },
    },
}


# ================================================================
# PER-TEMPLATE SHORT TAGLINES — pool indexed by template slug hash
# Each template gets ONE tagline from the pool deterministically.
# ================================================================
TEMPLATE_TAGLINE_POOLS = {
    'animal': {
        'en': [
            'Compassionate care, delivered with modern clarity',
            'A digital home for clinics that treat pets like family',
            'Warm design built around every wagging tail',
            'Where trust meets tender veterinary expertise',
            'Healing hands, heartfelt websites',
            'Built for the quiet heroes of animal care',
            'Premium presence for modern pet professionals',
            'A welcoming first impression for every pet parent',
        ],
        'it': [
            'Cura compassionevole, presentata con chiarezza moderna',
            'Una casa digitale per cliniche che trattano gli animali come famiglia',
            'Design caldo costruito attorno a ogni coda che scodinzola',
            'Dove la fiducia incontra la tenera esperienza veterinaria',
            'Mani che curano, siti dal cuore',
            'Pensato per gli eroi silenziosi della cura animale',
            'Presenza premium per i moderni professionisti degli animali',
            'Una prima impressione accogliente per ogni padrone',
        ],
        'fr': [
            'Des soins compatissants, une présentation moderne et limpide',
            'Un foyer digital pour cliniques qui traitent les animaux comme une famille',
            'Un design chaleureux pensé pour chaque queue qui remue',
            'Où la confiance rencontre la tendresse vétérinaire',
            'Des mains qui soignent, des sites qui touchent',
            'Conçu pour les héros discrets du soin animal',
            'Présence premium pour les pros du monde animal',
            'Une première impression accueillante pour chaque maître',
        ],
        'ar': [
            'رعاية حنونة تُقدَّم بوضوح حديث',
            'بيت رقمي للعيادات التي تعامل الحيوانات كعائلة',
            'تصميم دافئ يحتضن كل ذيل مبتهج',
            'حيث تلتقي الثقة بالخبرة البيطرية الحانية',
            'أيدٍ تشفي ومواقع تلمس القلب',
            'صُنع لأبطال رعاية الحيوان الصامتين',
            'حضور فاخر لمحترفي عالم الحيوان',
            'انطباع أول ترحيبي لكل صاحب حيوان',
        ],
    },
    'medical': {
        'en': [
            'Clinical clarity meets premium digital presence',
            'Inspire trust before patients walk through the door',
            'Calm, confident layouts for modern healthcare',
            'Where evidence-based medicine meets elegant design',
            'Reassuring design for every patient journey',
            'Professional websites built around patient care',
            'Healthcare excellence, beautifully presented',
            'Trust-building layouts for every specialty',
        ],
        'it': [
            'Chiarezza clinica incontra presenza digitale premium',
            'Ispira fiducia prima ancora che il paziente entri',
            'Layout calmi e sicuri per la sanità moderna',
            'Dove la medicina basata sulle evidenze incontra il design elegante',
            'Design rassicurante per ogni percorso del paziente',
            'Siti professionali costruiti attorno alla cura',
            'Eccellenza sanitaria, presentata con eleganza',
            'Layout che costruiscono fiducia in ogni specializzazione',
        ],
        'fr': [
            'Clarté clinique et présence digitale premium',
            'Inspirez confiance avant même l\'arrivée du patient',
            'Mises en page sereines et sûres pour la santé moderne',
            'Où la médecine fondée sur les preuves rencontre le design élégant',
            'Un design rassurant pour chaque parcours patient',
            'Des sites professionnels centrés sur le soin',
            'L\'excellence médicale, magnifiquement présentée',
            'Des mises en page qui installent la confiance, dans chaque spécialité',
        ],
        'ar': [
            'وضوح طبي وحضور رقمي فاخر',
            'ألهم الثقة قبل أن يدخل المريض من الباب',
            'تخطيطات هادئة وواثقة للرعاية الحديثة',
            'حيث يلتقي الطب المبني على الأدلة بالتصميم الأنيق',
            'تصميم مطمئن لكل رحلة مريض',
            'مواقع احترافية مبنية حول رعاية المريض',
            'تميّز طبي، مُقدَّم بأناقة',
            'تخطيطات تبني الثقة في كل تخصص',
        ],
    },
    'restaurant': {
        'en': [
            'Menus, reservations, and ambience — deliciously online',
            'Bring your kitchen\'s character to the web',
            'Taste, presented with editorial elegance',
            'Where hospitality meets pixel-perfect craft',
            'A digital welcome worthy of your cuisine',
            'Savor the story behind every dish',
            'Premium design, plated online',
            'Where every scroll feels like a tasting menu',
        ],
        'it': [
            'Menu, prenotazioni e atmosfera — deliziosamente online',
            'Porta il carattere della tua cucina sul web',
            'Il gusto, presentato con eleganza editoriale',
            'Dove l\'ospitalità incontra l\'arte del pixel',
            'Un benvenuto digitale degno della tua cucina',
            'Assapora la storia dietro ogni piatto',
            'Design premium, impiattato online',
            'Dove ogni scroll sembra un menu degustazione',
        ],
        'fr': [
            'Menus, réservations et ambiance — délicieusement en ligne',
            'Apportez le caractère de votre cuisine au web',
            'Le goût, présenté avec une élégance éditoriale',
            'Où l\'hospitalité rencontre l\'art du pixel',
            'Un accueil digital digne de votre cuisine',
            'Savourez l\'histoire derrière chaque plat',
            'Un design premium, dressé en ligne',
            'Où chaque scroll ressemble à un menu dégustation',
        ],
        'ar': [
            'قوائم وحجوزات وأجواء — لذيذة على الإنترنت',
            'انقل شخصية مطبخك إلى الويب',
            'المذاق يُقدَّم بأناقة تحريرية',
            'حيث تلتقي الضيافة بفن البكسل',
            'ترحيب رقمي يليق بمطبخك',
            'تذوّق القصة خلف كل طبق',
            'تصميم فاخر مُقدَّم عبر الإنترنت',
            'حيث يبدو كل تمرير للشاشة كقائمة تذوّق',
        ],
    },
    # Fallback for any category not listed above
    'default': {
        'en': [
            'Premium design, ready to be yours',
            'Crafted with care, built to convert',
            'Modern layouts, unmistakably premium',
            'A website that matches your ambition',
            'Hand-crafted design, dynamically yours',
            'Elegant, modern, immediately usable',
            'Professional presence, zero friction',
            'Built for the brands that want more',
        ],
        'it': [
            'Design premium, pronto a diventare tuo',
            'Curato nei dettagli, costruito per convertire',
            'Layout moderni, inequivocabilmente premium',
            'Un sito all\'altezza della tua ambizione',
            'Design artigianale, dinamicamente tuo',
            'Elegante, moderno, immediatamente utilizzabile',
            'Presenza professionale, zero attrito',
            'Pensato per i brand che vogliono di più',
        ],
        'fr': [
            'Un design premium, prêt à devenir le vôtre',
            'Soigné dans les détails, bâti pour convertir',
            'Des mises en page modernes, résolument premium',
            'Un site à la hauteur de votre ambition',
            'Un design artisanal, dynamiquement vôtre',
            'Élégant, moderne, immédiatement utilisable',
            'Une présence professionnelle, sans friction',
            'Conçu pour les marques qui veulent plus',
        ],
        'ar': [
            'تصميم فاخر جاهز ليصبح ملكك',
            'صُنع بعناية، بُني للتحويل',
            'تخطيطات حديثة، فاخرة بلا منازع',
            'موقع بمستوى طموحك',
            'تصميم حرفي، ديناميكي ملكك',
            'أنيق وحديث وقابل للاستخدام فوراً',
            'حضور احترافي بلا احتكاك',
            'صُنع للعلامات التي تريد المزيد',
        ],
    },
}


# ================================================================
# SMART "ABOUT THIS TEMPLATE" DESCRIPTIONS
# Per-category pool of 4 variants × 4 languages. Each template picks
# one variant deterministically via slug hash — so neighbors don't
# show identical copy.
# ================================================================
ABOUT_POOLS = {
    'animal': {
        'en': [
            '{name} is a premium veterinary and pet-care template crafted to communicate warmth, trust and professional expertise from the very first scroll. Built-in appointment flows, compassionate imagery and a calm, reassuring visual language make it the ideal digital home for clinics, shelters, groomers and specialists who want their online presence to match the quality of their care.',
            '{name} is engineered for modern animal-care professionals — veterinarians, pet boutiques, shelters and groomers — who need a premium digital presence that earns trust instantly. Every section is optimized to showcase services, highlight your team and streamline appointment booking, with a warmth that makes pet parents feel at home before they even walk through your door.',
            'Designed with compassion and built for conversion, {name} brings modern sensibility to pet-care websites. From emergency contact forms to adoption storytelling, each page is tuned to turn visitors into loyal clients — all while communicating the expertise, dedication and humanity that define great veterinary practices.',
            '{name} captures what modern pet-care clients demand: clarity, warmth, and effortless booking. Showcase your team, your services, your philosophy and your success stories through a layout that feels both professional and deeply human — the perfect bridge between clinical excellence and the heart that makes it matter.',
        ],
        'it': [
            '{name} è un template premium per la cura degli animali, progettato per comunicare calore, fiducia e professionalità fin dal primo scroll. Flussi di prenotazione integrati, immagini empatiche e un linguaggio visivo calmo e rassicurante lo rendono la casa digitale ideale per cliniche, rifugi, toelettatori e specialisti che vogliono una presenza online all\'altezza della loro cura.',
            '{name} è stato pensato per i moderni professionisti del mondo animale — veterinari, pet shop, rifugi e toelettatori — che hanno bisogno di una presenza digitale premium in grado di conquistare fiducia all\'istante. Ogni sezione è ottimizzata per mostrare i servizi, valorizzare il team e semplificare la prenotazione, con il calore che fa sentire ogni padrone a casa ancora prima di entrare.',
            'Progettato con empatia e costruito per la conversione, {name} porta la sensibilità moderna nei siti di cura animale. Dai moduli d\'emergenza allo storytelling sulle adozioni, ogni pagina è calibrata per trasformare visitatori in clienti fedeli — comunicando al tempo stesso la competenza, la dedizione e l\'umanità che definiscono le migliori cliniche veterinarie.',
            '{name} cattura ciò che i clienti moderni chiedono: chiarezza, calore e prenotazioni senza sforzo. Mostra il tuo team, i servizi, la filosofia e le storie di successo attraverso un layout che unisce professionalità e profonda umanità — il ponte perfetto tra eccellenza clinica e cuore che la rende davvero importante.',
        ],
        'fr': [
            '{name} est un template premium dédié à la santé animale, conçu pour transmettre chaleur, confiance et expertise professionnelle dès le premier regard. Parcours de rendez-vous intégrés, imagerie empathique et langage visuel apaisant en font le foyer digital idéal pour cliniques, refuges, toiletteurs et spécialistes qui veulent une présence en ligne à la hauteur de leurs soins.',
            '{name} est pensé pour les professionnels modernes du monde animal — vétérinaires, animaleries, refuges et toiletteurs — qui ont besoin d\'une présence digitale premium capable de gagner la confiance instantanément. Chaque section est optimisée pour mettre en avant les services, valoriser l\'équipe et simplifier la prise de rendez-vous, avec la chaleur qui fait se sentir chez lui tout propriétaire.',
            'Conçu avec empathie et bâti pour la conversion, {name} apporte une sensibilité moderne aux sites de santé animale. Des formulaires d\'urgence aux récits d\'adoption, chaque page est calibrée pour transformer les visiteurs en clients fidèles — en communiquant l\'expertise, le dévouement et l\'humanité qui définissent les meilleures cliniques.',
            '{name} capture tout ce que les clients modernes attendent : clarté, chaleur et prise de rendez-vous sans effort. Mettez en valeur votre équipe, vos services, votre philosophie et vos réussites grâce à une mise en page qui allie professionnalisme et profonde humanité — le pont parfait entre excellence clinique et cœur.',
        ],
        'ar': [
            '{name} قالب فاخر مخصّص لرعاية الحيوانات، صُنع ليوصِل الدفء والثقة والخبرة المهنية منذ اللحظة الأولى. تتكامل فيه أنظمة الحجز والصور المُعبّرة واللغة البصرية الهادئة ليكون البيت الرقمي المثالي للعيادات والملاجئ وخبراء العناية الذين يريدون حضوراً إلكترونياً بمستوى رعايتهم.',
            'صُمّم {name} للمحترفين المعاصرين في عالم الحيوان — أطباء بيطريون ومتاجر حيوانات وملاجئ وخبراء تجميل — الذين يحتاجون حضوراً رقمياً فاخراً يكسب الثقة فوراً. كل قسم مُحسَّن لعرض الخدمات وإبراز الفريق وتبسيط الحجز، بدفء يشعر معه كل صاحب حيوان أنه في بيته.',
            'مُصمَّم برحمة ومبني للتحويل، يُدخل {name} حساسية حديثة إلى مواقع رعاية الحيوان. من نماذج الطوارئ إلى قصص التبنّي، كل صفحة مضبوطة لتحويل الزائرين إلى عملاء دائمين — مع إيصال الخبرة والتفاني والإنسانية التي تُعرِّف أفضل العيادات البيطرية.',
            '{name} يلتقط ما يطلبه عملاء اليوم: الوضوح والدفء والحجز السلس. اعرض فريقك وخدماتك وفلسفتك وقصص نجاحك عبر تخطيط يجمع بين الاحترافية والإنسانية العميقة — الجسر المثالي بين التميز الطبي والقلب الذي يجعله مهمّاً.',
        ],
    },
    'medical': {
        'en': [
            '{name} is a professional healthcare template engineered to inspire trust before patients even pick up the phone. Clean diagnostics-friendly layouts, appointment flows, specialty pages and reassuring visual language turn your digital presence into the credible extension of your clinical excellence.',
            '{name} blends clinical rigor with premium digital craft. Designed for hospitals, clinics, dentists and wellness specialists, it features appointment-first architecture, doctor showcases, department pages and testimonial modules — everything you need to let your expertise lead the conversation online.',
            'Every detail of {name} is tuned for healthcare credibility: calm palettes, accessible typography, structured service descriptions and frictionless appointment flows. Whether you\'re a single practitioner or a multi-department facility, this template scales to meet your communication needs without ever compromising on clarity.',
            '{name} is your digital waiting room — calm, competent, and confident. Built around patient-first design principles, it showcases your team, your specialties, your facilities and your care pathways with the kind of elegant restraint that serious healthcare brands deserve.',
        ],
        'it': [
            '{name} è un template sanitario professionale progettato per ispirare fiducia ancor prima che il paziente sollevi il telefono. Layout puliti e diagnostici, flussi di prenotazione, pagine di specialità e un linguaggio visivo rassicurante trasformano la tua presenza digitale nell\'estensione credibile della tua eccellenza clinica.',
            '{name} unisce rigore clinico e artigianato digitale premium. Pensato per ospedali, cliniche, dentisti e specialisti del benessere, offre un\'architettura orientata alle prenotazioni, showcase dei medici, pagine dei reparti e moduli testimonianze — tutto ciò che serve per far parlare la tua competenza online.',
            'Ogni dettaglio di {name} è calibrato per la credibilità sanitaria: palette calme, tipografia accessibile, descrizioni strutturate dei servizi e flussi di prenotazione senza attriti. Che tu sia un professionista singolo o una struttura multidipartimento, questo template scala per rispondere alle tue esigenze di comunicazione senza mai compromettere la chiarezza.',
            '{name} è la tua sala d\'attesa digitale — calma, competente e sicura. Costruito attorno ai principi di design patient-first, mostra il tuo team, le specialità, le strutture e i percorsi di cura con l\'eleganza sobria che i brand sanitari seri meritano.',
        ],
        'fr': [
            '{name} est un template médical professionnel conçu pour inspirer confiance avant même que le patient ne décroche son téléphone. Des mises en page nettes et compatibles avec la rigueur diagnostique, des parcours de rendez-vous, des pages de spécialités et un langage visuel rassurant font de votre présence digitale l\'extension crédible de votre excellence clinique.',
            '{name} allie rigueur clinique et artisanat digital premium. Conçu pour hôpitaux, cliniques, dentistes et spécialistes du bien-être, il propose une architecture centrée sur la prise de rendez-vous, des mises en avant de médecins, des pages de départements et des modules de témoignages — tout ce dont vous avez besoin pour laisser votre expertise mener la conversation en ligne.',
            'Chaque détail de {name} est calibré pour la crédibilité médicale : palettes apaisantes, typographie accessible, descriptions structurées des services et parcours de rendez-vous sans friction. Que vous soyez praticien unique ou structure multidépartementale, ce template évolue avec vos besoins sans jamais sacrifier la clarté.',
            '{name} est votre salle d\'attente digitale — sereine, compétente, confiante. Bâti sur les principes du patient-first design, il met en valeur votre équipe, vos spécialités, vos installations et vos parcours de soin avec l\'élégance sobre que méritent les marques médicales sérieuses.',
        ],
        'ar': [
            '{name} قالب طبي احترافي مصمّم ليُلهم الثقة قبل أن يرفع المريض سماعة الهاتف. تخطيطات نظيفة ومريحة للعمل السريري، وأنظمة حجز، وصفحات تخصّصات، ولغة بصرية مطمئنة، تحوّل حضورك الرقمي إلى امتداد موثوق لتميّزك الطبي.',
            'يجمع {name} بين الصرامة الطبية والصنعة الرقمية الفاخرة. مصمّم للمستشفيات والعيادات وأطباء الأسنان ومتخصّصي العافية، ويقدّم هيكلية مركّزة على الحجز، وصفحات للأطباء والأقسام، ونماذج شهادات — كل ما تحتاجه لتتحدث خبرتك أولاً على الإنترنت.',
            'كل تفصيل في {name} مضبوط من أجل المصداقية الطبية: ألوان هادئة وخطوط سهلة القراءة ووصف منظَّم للخدمات وحجوزات بلا احتكاك. سواء كنت طبيباً منفرداً أو مؤسسة متعدّدة الأقسام، يتكيّف هذا القالب مع احتياجاتك دون المساومة على الوضوح.',
            '{name} غرفة انتظارك الرقمية — هادئة، مختصّة، واثقة. مبني على مبادئ التصميم المتمحور حول المريض، يُبرز فريقك وتخصّصاتك ومرافقك ومسارات الرعاية بالأناقة الرصينة التي تستحقها العلامات الطبية الجادة.',
        ],
    },
    'restaurant': {
        'en': [
            '{name} is an appetizing restaurant template crafted to bring the character of your kitchen to the web. Editorial menu layouts, atmospheric galleries, reservation flows and chef stories combine to create a digital welcome as warm as your dining room — the perfect hors d\'oeuvre before the real meal.',
            '{name} plates your cuisine online with the same care you bring to every dish. From seasonal menus to private-event pages, from chef introductions to frictionless table bookings, every element is tuned to turn scrollers into diners and diners into regulars who bring their friends.',
            'Taste, atmosphere, hospitality — {name} translates all three into a digital experience worthy of your kitchen. Editorial imagery, menu showcases, reservation shortcuts and location details come together in a layout that reads like a beautifully designed menu and feels like a warm table for two.',
            '{name} is the digital extension of your hospitality. Built for restaurants, bistros, cafés and culinary brands that take pride in craft, it places your menu, your chef, your story and your reservation system at the center of the experience — with the editorial elegance that gourmet clients expect.',
        ],
        'it': [
            '{name} è un template appetitoso per ristoranti, creato per portare il carattere della tua cucina sul web. Layout editoriali del menu, gallerie d\'atmosfera, flussi di prenotazione e storie degli chef si combinano per creare un benvenuto digitale caldo quanto la tua sala — l\'antipasto perfetto prima del vero pasto.',
            '{name} impiatta la tua cucina online con la stessa cura che metti in ogni piatto. Dai menu stagionali alle pagine per eventi privati, dalle presentazioni dello chef alle prenotazioni senza attriti, ogni elemento è calibrato per trasformare gli scroller in clienti e i clienti in habitué che portano gli amici.',
            'Gusto, atmosfera, ospitalità — {name} traduce tutti e tre in un\'esperienza digitale degna della tua cucina. Immagini editoriali, showcase del menu, scorciatoie per le prenotazioni e dettagli della location si uniscono in un layout che si legge come un menu ben disegnato e sa di tavolo caldo per due.',
            '{name} è l\'estensione digitale della tua ospitalità. Pensato per ristoranti, bistrot, caffè e brand gastronomici che fanno dell\'arte una missione, mette al centro dell\'esperienza il tuo menu, il tuo chef, la tua storia e il sistema di prenotazione — con l\'eleganza editoriale che i clienti gourmet si aspettano.',
        ],
        'fr': [
            '{name} est un template de restaurant appétissant, conçu pour apporter le caractère de votre cuisine au web. Mises en page éditoriales du menu, galeries d\'ambiance, parcours de réservation et récits de chef se combinent pour créer un accueil digital aussi chaleureux que votre salle — l\'amuse-bouche parfait avant le vrai repas.',
            '{name} dresse votre cuisine en ligne avec le même soin que chaque assiette. Des menus de saison aux pages d\'événements privés, des présentations de chef aux réservations sans friction, chaque élément est calibré pour transformer les scrolleurs en convives et les convives en habitués qui amènent leurs amis.',
            'Goût, ambiance, hospitalité — {name} traduit les trois en une expérience digitale digne de votre cuisine. Imagerie éditoriale, vitrines de menu, raccourcis de réservation et détails de localisation s\'assemblent en une mise en page qui se lit comme un menu bien conçu et se ressent comme une table chaleureuse.',
            '{name} est l\'extension digitale de votre hospitalité. Conçu pour restaurants, bistrots, cafés et marques culinaires qui font de leur métier un art, il place votre menu, votre chef, votre histoire et votre système de réservation au cœur de l\'expérience — avec l\'élégance éditoriale qu\'attendent les clients gourmets.',
        ],
        'ar': [
            '{name} قالب مطاعم شهيّ صُنع ليحمل شخصية مطبخك إلى الويب. تخطيطات تحريرية للقائمة ومعارض أجواء وأنظمة حجز وقصص شيفات تجتمع لتخلق ترحيباً رقمياً بدفء قاعتك — المقبّلات المثالية قبل الوجبة الحقيقية.',
            'يُقدّم {name} مطبخك عبر الإنترنت بالعناية ذاتها التي تضعها في كل طبق. من القوائم الموسمية إلى صفحات المناسبات الخاصة، ومن تعريفات الشيف إلى الحجوزات السلسة، كل عنصر مضبوط ليحوّل المتصفّح إلى ضيف والضيف إلى زائر منتظم يصطحب أصدقاءه.',
            'مذاق وأجواء وضيافة — يترجم {name} الثلاثة إلى تجربة رقمية تليق بمطبخك. صور تحريرية وعرض قوائم واختصارات حجز وتفاصيل الموقع تجتمع في تخطيط يُقرأ كقائمة أنيقة ويُحسّ كطاولة دافئة لشخصين.',
            '{name} امتداد رقمي لضيافتك. مصمّم للمطاعم والبيسترو والمقاهي والعلامات الطهوية التي تعتبر صنعتها فنّاً، يضع قائمتك وشيفك وقصتك ونظام الحجز في قلب التجربة — بالأناقة التحريرية التي يتوقعها عشاق الذواقة.',
        ],
    },
    # Generic fallback pool for any category not covered above
    'default': {
        'en': [
            '{name} is a premium, fully customizable template designed to give modern professionals a digital presence that matches their ambition. Every section — from hero to footer — is crafted for clarity, conversion and effortless personalization, so your brand takes center stage from the first scroll.',
            '{name} combines refined aesthetics with conversion-optimized architecture. Built for businesses that want to look premium without the agency price tag, it delivers a complete, responsive, accessible digital foundation you can make entirely your own in minutes.',
            'Designed for discerning professionals, {name} offers a perfect balance between editorial elegance and commercial clarity. Feature your services, showcase your work, capture leads and build trust — all through a layout engineered to turn casual visitors into committed clients.',
            '{name} is more than a template — it\'s a complete, production-ready digital presence waiting for your brand. Modern typography, thoughtful spacing, premium imagery support and a conversion-first structure make it the ideal starting point for businesses that refuse to blend in.',
        ],
        'it': [
            '{name} è un template premium completamente personalizzabile, progettato per offrire ai professionisti moderni una presenza digitale all\'altezza della loro ambizione. Ogni sezione — dall\'hero al footer — è costruita per chiarezza, conversione e personalizzazione senza sforzo, così il tuo brand è protagonista fin dal primo scroll.',
            '{name} unisce un\'estetica raffinata a un\'architettura ottimizzata per la conversione. Pensato per le attività che vogliono apparire premium senza i costi d\'agenzia, offre una base digitale completa, responsive e accessibile che puoi rendere interamente tua in pochi minuti.',
            'Progettato per professionisti esigenti, {name} offre il perfetto equilibrio tra eleganza editoriale e chiarezza commerciale. Mostra i servizi, presenta il tuo lavoro, cattura contatti e costruisci fiducia — tutto attraverso un layout pensato per trasformare i visitatori occasionali in clienti convinti.',
            '{name} è più di un template — è una presenza digitale completa, pronta per la produzione, in attesa del tuo brand. Tipografia moderna, spaziature ponderate, supporto per immagini premium e una struttura conversion-first lo rendono il punto di partenza ideale per le attività che non vogliono confondersi nella massa.',
        ],
        'fr': [
            '{name} est un template premium entièrement personnalisable, pensé pour offrir aux professionnels modernes une présence digitale à la hauteur de leur ambition. Chaque section — du hero au footer — est conçue pour la clarté, la conversion et une personnalisation sans effort, pour que votre marque occupe le devant de la scène dès le premier coup d\'œil.',
            '{name} allie une esthétique raffinée à une architecture optimisée pour la conversion. Conçu pour les entreprises qui veulent paraître premium sans les tarifs d\'agence, il offre une base digitale complète, responsive et accessible que vous pouvez vous approprier entièrement en quelques minutes.',
            'Pensé pour les professionnels exigeants, {name} offre l\'équilibre parfait entre élégance éditoriale et clarté commerciale. Mettez en valeur vos services, présentez votre travail, captez des leads et bâtissez la confiance — le tout à travers une mise en page conçue pour transformer les visiteurs occasionnels en clients engagés.',
            '{name} est plus qu\'un template — c\'est une présence digitale complète, prête pour la production, qui n\'attend que votre marque. Typographie moderne, espacements réfléchis, support d\'imagerie premium et structure conversion-first en font le point de départ idéal pour les entreprises qui refusent de se fondre dans la masse.',
        ],
        'ar': [
            '{name} قالب فاخر قابل للتخصيص بالكامل، صُمّم ليمنح المحترفين المعاصرين حضوراً رقمياً بمستوى طموحهم. كل قسم — من الهيدر إلى التذييل — صُنع من أجل الوضوح والتحويل والتخصيص السلس، ليكون براندك في قلب المشهد من اللحظة الأولى.',
            'يجمع {name} بين جمالية راقية وهيكلية مُحسَّنة للتحويل. مصمّم للأعمال التي تريد حضوراً فاخراً دون تكاليف الوكالات، يقدّم قاعدة رقمية كاملة ومتجاوبة ويمكن الوصول إليها يمكنك أن تجعلها ملكك بالكامل في دقائق.',
            'مصمّم للمحترفين المتميّزين، يقدّم {name} التوازن المثالي بين الأناقة التحريرية والوضوح التجاري. اعرض خدماتك وأعمالك واجمع العملاء المحتملين وابنِ الثقة — كل ذلك عبر تخطيط مبني لتحويل الزائر العابر إلى عميل ملتزم.',
            '{name} أكثر من قالب — إنه حضور رقمي كامل جاهز للإنتاج بانتظار علامتك. خطوط حديثة ومسافات مدروسة ودعم للصور الفاخرة وهيكلية تركّز على التحويل تجعله نقطة الانطلاق المثالية للأعمال التي ترفض الذوبان في القطيع.',
        ],
    },
}


# Map category slug → pool key (so CategoryContent.slug='real-estate' → 'real-estate')
def _slug_key(slug_or_name: str) -> str:
    if not slug_or_name:
        return 'default'
    s = str(slug_or_name).lower().replace(' ', '-').replace('_', '-').replace('&', 'and')
    return s


def get_category_content(category, locale='en'):
    """Return {tagline, description} for a category in the given locale."""
    if not category:
        return {'tagline': '', 'description': ''}
    key = _slug_key(getattr(category, 'slug', '') or getattr(category, 'name', ''))
    content = CATEGORY_CONTENT.get(key)
    if not content:
        return {
            'tagline': getattr(category, 'tagline', '') or '',
            'description': getattr(category, 'description', '') or '',
        }
    return content.get(locale, content.get('en', {'tagline': '', 'description': ''}))


def get_template_tagline(template, locale='en'):
    """Return a deterministic per-template tagline in the given locale."""
    if not template:
        return ''
    try:
        cat_key = _slug_key(template.category.slug)
    except Exception:
        cat_key = 'default'
    pool = TEMPLATE_TAGLINE_POOLS.get(cat_key) or TEMPLATE_TAGLINE_POOLS['default']
    items = pool.get(locale) or pool.get('en') or ['']
    seed = sum(ord(c) for c in getattr(template, 'slug', '') or '')
    return items[seed % len(items)]


def get_template_about(template, locale='en'):
    """Return a deterministic per-template 'About this template' text in the
    given locale, with the template name interpolated in."""
    if not template:
        return ''
    try:
        cat_key = _slug_key(template.category.slug)
    except Exception:
        cat_key = 'default'
    pool = ABOUT_POOLS.get(cat_key) or ABOUT_POOLS['default']
    items = pool.get(locale) or pool.get('en') or ['']
    seed = sum(ord(c) for c in getattr(template, 'slug', '') or '')
    chosen = items[seed % len(items)]
    return chosen.format(name=getattr(template, 'name', 'This template'))
