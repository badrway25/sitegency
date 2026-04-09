"""
Seed the marketplace with FAQs, testimonials, and site config.
Run after `import_templates`.
"""
from django.core.management.base import BaseCommand
from core.models import SiteConfig, FAQ, Testimonial


FAQ_DATA = [
    ('Can I really customize everything before I buy?',
     'Yes. Every template ships with a live customizer where you can swap your logo, colors, '
     'headlines, photos, contact details and social links in real time. The preview updates '
     'instantly in your browser — you see exactly what you\'re getting before you pay a cent.'),
    ('What exactly am I buying?',
     'You\'re buying a complete, production-ready website package: HTML, CSS, JavaScript, fonts, '
     'images, and all assets. You own the code and the commercial license for one project. '
     'You can deploy anywhere — your own hosting, Netlify, Vercel, AWS, anywhere.'),
    ('Do I need to know how to code?',
     'No. Our live customizer handles logo uploads, color changes, text edits and image swaps '
     'without touching code. If you want to dig deeper, the source is yours — clean, documented, '
     'and built to modern standards.'),
    ('How is Sitegency different from ThemeForest or TemplateMonster?',
     'Three things: (1) you can actually navigate every page of a template before buying — '
     'no more screenshots that lie; (2) you customize with your real data inside our live '
     'editor, not after downloading; (3) every template is curated, refined and modernized '
     'in-house. No recycled garbage.'),
    ('Why is the marketplace built on Django?',
     'Django is the gold standard for secure, scalable web platforms. NASA, Instagram, Spotify '
     'and Pinterest run on it. We chose Django because your checkout, your customization data '
     'and your downloads deserve the same enterprise-grade foundation the world\'s biggest '
     'platforms trust.'),
    ('What does the license allow?',
     'A Single Project license lets you deploy the template on one domain for one business '
     'or client. Need more? Our Extended and Unlimited licenses cover agencies, freelancers '
     'and teams running multiple projects.'),
    ('Do you offer refunds?',
     'Yes. Every purchase is protected by a 14-day refund policy. If the template doesn\'t meet '
     'your expectations, contact support and we make it right — no questions asked.'),
    ('How long does it take to launch a site?',
     'Most customers go from browsing to live site in under 60 minutes. Pick a template, '
     'drop in your content through the customizer, download the package, upload to your host. '
     'That\'s it.'),
    ('Do I get updates?',
     'Yes. Every template includes 6 months of free updates — security patches, browser '
     'compatibility fixes, and minor enhancements. Major version upgrades are available at '
     'a reduced rate.'),
    ('Can I preview on mobile?',
     'Absolutely. Our preview engine and customizer both include desktop, tablet and mobile '
     'viewports. Every template is responsive by default, rigorously tested across devices.'),
]


TESTIMONIALS = [
    ('Sarah Johnson', 'Founder', 'PawCentral Veterinary', 5,
     'I launched my clinic website in two hours. Two hours! The customizer let me drop in our '
     'logo, photos and services while I watched the site come to life. My patients love it.'),
    ('Marcus Chen', 'Creative Director', 'Studio Nine', 5,
     'As an agency, we use Sitegency for rapid client prototyping. The quality is genuinely '
     'premium — not the usual template marketplace junk. Our clients can\'t believe we didn\'t '
     'build from scratch.'),
    ('Elena Rodriguez', 'Owner', 'Bistro Saveur', 5,
     'Before Sitegency, I was quoted €8000 by three agencies. I spent €79 here, previewed the '
     'exact site before buying, and launched the same day. The template is stunning.'),
    ('Dr. Ahmed Hassan', 'Founder', 'NovaMed Clinic', 5,
     'The fact that I could navigate every page before buying was a game-changer. No surprises, '
     'no hidden ugly pages. What I saw is what I got. And the live customizer is magic.'),
    ('Priya Patel', 'Freelance Designer', 'Patel Design Co', 5,
     'I use Sitegency templates as starting points for my own client projects. The code quality '
     'is clean, the design is genuinely modern, and my clients get a beautiful site fast.'),
    ('Jacob Weiss', 'Real Estate Broker', 'Skyline Properties', 5,
     'Shopped three marketplaces. Only Sitegency let me actually click through every page. Bought '
     'within 15 minutes. My listings have never looked better.'),
]


class Command(BaseCommand):
    help = "Seed FAQs, testimonials, and site config."

    def handle(self, *args, **options):
        SiteConfig.get_solo()
        self.stdout.write(self.style.SUCCESS("✔ Site config ready"))

        FAQ.objects.all().delete()
        for i, (q, a) in enumerate(FAQ_DATA):
            FAQ.objects.create(question=q, answer=a, order=i * 10)
        self.stdout.write(self.style.SUCCESS(f"✔ {len(FAQ_DATA)} FAQs created"))

        Testimonial.objects.all().delete()
        for i, (name, role, company, rating, content) in enumerate(TESTIMONIALS):
            Testimonial.objects.create(
                author_name=name, author_role=role, author_company=company,
                rating=rating, content=content, is_featured=True, order=i * 10,
            )
        self.stdout.write(self.style.SUCCESS(f"✔ {len(TESTIMONIALS)} testimonials created"))
        self.stdout.write(self.style.SUCCESS("\n✨ Seed complete. Now run: python manage.py import_templates"))
