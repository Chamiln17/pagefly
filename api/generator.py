from .schemas import LandingPageParams
# Bridge with the AGENTIC AI

def generate_landing_page(data: LandingPageParams) -> str:
    return """
    <!DOCTYPE html>
    <html lang="ar" dir="rtl">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>تألق شعرك مع Brosse Lissante ENZO EN-4102.1</title>
        <meta name="description" content="احصلي على شعر ناعم ومستقيم بكفاءة صالون التجميل في دقائق باستخدام Brosse Lissante ENZO EN-4102.1. اختاري التصفيف السريع والاحترافي بسعر 4500.0 DZD الآن!">
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
        <link href="https://fonts.googleapis.com/css2?family=Tajawal:wght@400;500;700&display=swap" rel="stylesheet">
        <style>
            :root {
                --color-primary: #ABAB70;
                --color-secondary: #6F9024;
                --color-bg-light: #E0E6D5;
                --color-neutral: #B0BCA0;
                --color-accent: #859A57;
                --color-highlight: #ABAB70;
                --transition-standard: all 0.3s ease;
                --shadow-standard: 0 4px 12px rgba(0, 0, 0, 0.1);
            }
            
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            
            body {
                font-family: 'Tajawal', sans-serif;
                background-color: var(--color-bg-light);
                color: #333;
                line-height: 1.6;
                overflow-x: hidden;
            }
            
            img {
                max-width: 100%;
                height: auto;
                border-radius: 8px;
                display: block;
            }
            
            .container {
                width: 100%;
                max-width: 1200px;
                margin: 0 auto;
                padding: 0 1rem;
            }
            
            header {
                background-color: var(--color-primary);
                padding: 1rem 0;
                box-shadow: var(--shadow-standard);
                position: sticky;
                top: 0;
                z-index: 100;
            }
            
            header .container {
                display: flex;
                justify-content: space-between;
                align-items: center;
            }
            
            .logo {
                font-size: clamp(1.5rem, 5vw, 2.5rem);
                font-weight: 700;
                color: white;
            }
            
            .section {
                padding: 3rem 0;
                opacity: 0;
                transform: translateY(20px);
                transition: var(--transition-standard);
            }
            
            .section.visible {
                opacity: 1;
                transform: translateY(0);
            }
            
            h1, h2, h3, h4 {
                color: var(--color-secondary);
                margin-bottom: 1.5rem;
                line-height: 1.3;
            }
            
            h1 {
                font-size: clamp(2rem, 6vw, 3.5rem);
            }
            
            h2 {
                font-size: clamp(1.8rem, 5vw, 3rem);
            }
            
            h3 {
                font-size: clamp(1.5rem, 4vw, 2.5rem);
            }
            
            p {
                margin-bottom: 1rem;
                font-size: clamp(1rem, 2.5vw, 1.2rem);
            }
            
            .btn {
                display: inline-block;
                background-color: var(--color-secondary);
                color: white;
                padding: 0.8rem 2rem;
                border-radius: 50px;
                text-decoration: none;
                font-weight: 700;
                font-size: clamp(1rem, 2.5vw, 1.3rem);
                transition: var(--transition-standard);
                border: none;
                cursor: pointer;
                box-shadow: var(--shadow-standard);
                text-align: center;
            }
            
            .btn:hover {
                background-color: var(--color-accent);
                transform: translateY(-3px);
                box-shadow: 0 6px 15px rgba(0, 0, 0, 0.15);
            }
            
            .btn.pulse {
                animation: pulse 2s infinite;
            }
            
            @keyframes pulse {
                0% {
                    box-shadow: 0 0 0 0 rgba(111, 144, 36, 0.7);
                }
                70% {
                    box-shadow: 0 0 0 10px rgba(111, 144, 36, 0);
                }
                100% {
                    box-shadow: 0 0 0 0 rgba(111, 144, 36, 0);
                }
            }
            
            /* Hero Section */
            .hero {
                min-height: 90vh;
                display: flex;
                align-items: center;
                background: linear-gradient(to bottom, var(--color-bg-light), white);
                position: relative;
            }
            
            .hero-content {
                text-align: center;
            }
            
            .hero-headlines {
                margin-bottom: 2rem;
            }
            
            .hero-headline {
                font-size: clamp(1.2rem, 3.5vw, 2rem);
                margin-bottom: 1rem;
                color: var(--color-secondary);
                font-weight: 700;
            }
            
            .hero-headline img {
                margin: 1.5rem auto;
                max-width: 80%;
                box-shadow: var(--shadow-standard);
            }
            
            /* Story Section */
            .story {
                background-color: white;
            }
            
            .story-content {
                display: grid;
                grid-template-columns: 1fr;
                gap: 2rem;
            }
            
            .story-content img {
                margin: 1.5rem auto;
                box-shadow: var(--shadow-standard);
            }
            
            /* Features Section */
            .features {
                background-color: var(--color-bg-light);
            }
            
            .feature-table {
                display: grid;
                grid-template-columns: 1fr;
                gap: 1.5rem;
            }
            
            .feature-item {
                background-color: white;
                padding: 1.5rem;
                border-radius: 12px;
                box-shadow: var(--shadow-standard);
                transition: var(--transition-standard);
            }
            
            .feature-item:hover {
                transform: translateY(-5px);
                box-shadow: 0 8px 20px rgba(0, 0, 0, 0.15);
            }
            
            .feature-name {
                font-size: clamp(1.1rem, 3vw, 1.5rem);
                color: var(--color-secondary);
                font-weight: 700;
                margin-bottom: 0.8rem;
            }
            
            .feature-benefit {
                font-size: clamp(0.9rem, 2.5vw, 1.1rem);
            }
            
            .feature-item img {
                margin: 1rem auto;
            }
            
            /* Price Section */
            .price {
                background-color: white;
                text-align: center;
            }
            
            .price-box {
                background-color: var(--color-bg-light);
                padding: 2rem;
                border-radius: 12px;
                box-shadow: var(--shadow-standard);
                display: inline-block;
                margin: 0 auto;
            }
            
            .price-current {
                font-size: clamp(2rem, 7vw, 3.5rem);
                font-weight: 700;
                color: var(--color-secondary);
            }
            
            .price-old {
                font-size: clamp(1.3rem, 4vw, 2rem);
                text-decoration: line-through;
                color: #888;
                margin-bottom: 1rem;
            }
            
            .price-save {
                font-size: clamp(1rem, 3vw, 1.5rem);
                background-color: var(--color-primary);
                color: white;
                padding: 0.5rem 1rem;
                border-radius: 50px;
                display: inline-block;
                margin-bottom: 1.5rem;
            }
            
            /* Guarantee Section */
            .guarantee {
                background-color: var(--color-bg-light);
            }
            
            .guarantee-content {
                text-align: center;
            }
            
            .guarantee-list {
                list-style: none;
                margin: 2rem 0;
            }
            
            .guarantee-item {
                font-size: clamp(1rem, 2.8vw, 1.3rem);
                margin-bottom: 1rem;
                position: relative;
                padding-right: 2rem;
                display: flex;
                align-items: center;
                justify-content: center;
            }
            
            .guarantee-item:before {
                content: "✓";
                position: absolute;
                right: 0;
                color: var(--color-secondary);
                font-weight: bold;
            }
            
            .guarantee-item img {
                margin: 1rem auto;
            }
            
            /* FAQ Section */
            .faq {
                background-color: white;
            }
            
            .faq-item {
                margin-bottom: 1.5rem;
                border-bottom: 1px solid var(--color-neutral);
                padding-bottom: 1.5rem;
            }
            
            .faq-question {
                font-size: clamp(1.1rem, 3vw, 1.4rem);
                font-weight: 700;
                color: var(--color-secondary);
                margin-bottom: 0.8rem;
                cursor: pointer;
                position: relative;
                padding-right: 1.5rem;
            }
            
            .faq-question:after {
                content: "+";
                position: absolute;
                right: 0;
                transition: var(--transition-standard);
            }
            
            .faq-question.active:after {
                transform: rotate(45deg);
            }
            
            .faq-answer {
                font-size: clamp(0.9rem, 2.5vw, 1.1rem);
                display: none;
            }
            
            .faq-answer.visible {
                display: block;
            }
            
            .faq-answer img {
                margin: 1rem auto;
            }
            
            /* Final CTA Section */
            .final-cta {
                background: linear-gradient(to top, var(--color-bg-light), white);
                text-align: center;
            }
            
            .final-cta h2 {
                margin-bottom: 2rem;
            }
            
            .final-cta img {
                margin: 1.5rem auto;
                max-width: 80%;
                box-shadow: var(--shadow-standard);
            }
            
            /* Footer */
            footer {
                background-color: var(--color-primary);
                color: white;
                padding: 2rem 0;
                text-align: center;
            }
            
            @media screen and (min-width: 768px) {
                .hero-headlines {
                    display: grid;
                    grid-template-columns: 1fr 1fr;
                    gap: 1.5rem;
                    align-items: center;
                }
                
                .story-content {
                    grid-template-columns: 1fr 1fr;
                    align-items: center;
                }
                
                .feature-table {
                    grid-template-columns: 1fr 1fr;
                }
            }
            
            @media screen and (min-width: 1024px) {
                .feature-table {
                    grid-template-columns: repeat(2, 1fr);
                }
                
                .hero-headlines {
                    grid-template-columns: repeat(3, 1fr);
                }
            }
        </style>
    </head>
    <body>
        <header>
            <div class="container">
                <div class="logo">ENZO</div>
                <a href="#cta" class="btn">اشتري الآن</a>
            </div>
        </header>
        
        <section class="section hero" id="hero">
            <div class="container">
                <div class="hero-content">
                    <h1>تألق شعرك مع Brosse Lissante ENZO EN-4102.1</h1>
                    <div class="hero-headlines">
                        <div class="hero-headline">نتائج صالون مبهرة <img src="https://example.com/product-image.jpg" alt="Mint green ENZO Advanced Straight Hair Comb with black bristles and gold tips. Measures 29 cm long, 6.5 x 6 cm head. Box dimensions: 37 x 11 cm. Box features product image, brand name, and 'UP to 98°F' label. Background is soft green."></div>
                        <div class="hero-headline">تصفيف سريع بفعالية عالية</div>
                        <div class="hero-headline">تقنية Proheat المتطورة</div>
                        <div class="hero-headline">تحكم ذكي بدرجة الحرارة</div>
                        <div class="hero-headline">شعر ناعم ومسطح فوراً</div>
                    </div>
                    <a href="#cta" class="btn pulse">اشتري الآن</a>
                </div>
            </div>
        </section>
        
        <section class="section story" id="story">
            <div class="container">
                <h2>تجربة تحول الشعر</h2>
                <div class="story-content">
                    <p>تحولي تجربتك مع الشعر المملوء بالتحديات إلى جمال مبهر. كانت معاناتك اليومية مع التجاعيد والتشابك تعرقل إطلالتك، ولكن مع Brosse Lissante ENZO EN-4102.1 أصبح التغيير سهلًا وسريعًا. تقنية Proheat والتحكم الذكي بدرجة الحرارة يمنحانك نتائج صالون احترافية خلال دقائق معدودة. <img src="https://example.com/product-image.jpg" alt="ENZO Professional Advanced Straight Hair Comb in mint green with gold details. Features black bristles, a temperature display (98.0°C & 60.0°C), and three control buttons. Includes a woman with sleek hair and 'Proheat Technology' for lasting salon results."> استمتعي بتحويل شعرك إلى شرارة من النعومة والإشراق كما لو كنتِ في صالون التجميل. <img src="https://example.com/product-image.jpg" alt="Two mint green brush-shaped tools rest on a light wooden surface. One is basic with cream-tipped bristles and gold base; the other has a display, gold buttons, and ENZO branding. Green leaves and calligraphy accent the clean background."></p>
                </div>
            </div>
        </section>
        
        <section class="section features" id="features">
            <div class="container">
                <h2>المميزات الفريدة</h2>
                <div class="feature-table">
                    <div class="feature-item">
                        <div class="feature-name">تقنية Proheat المتطورة</div>
                        <div class="feature-benefit">تسخين سريع يختصر وقتك لتحقيق تصفيف فوري.</div>
                    </div>
                    <div class="feature-item">
                        <div class="feature-name">تحكم ذكي بدرجة الحرارة</div>
                        <div class="feature-benefit">يحمي شعرك ويضمن نتائج متناسقة واحترافية. <img src="https://example.com/product-image.jpg" alt="Two mint green ENZO hair tools shown upright with black bristles and gold tips. One shows a 390°F display and buttons; the other shows the bristle side. Both have gold accents and cords, set against a fresh leafy backdrop."></div>
                    </div>
                    <div class="feature-item">
                        <div class="feature-name">تصميم عالي الأداء</div>
                        <div class="feature-benefit">يحاكي نتائج صالون التجميل بلمسة احترافية تبرز أناقتك.</div>
                    </div>
                    <div class="feature-item">
                        <div class="feature-name">راحة وسهولة الاستخدام</div>
                        <div class="feature-benefit">خفة الوزن وتنقّل سلس لتصفيف مثالي في المنزل أو أثناء السفر.</div>
                    </div>
                </div>
            </div>
        </section>
        
        <section class="section price" id="price">
            <div class="container">
                <h2>سعر خاص محدود</h2>
                <div class="price-box">
                    <div class="price-save">وفري 1500.0 DZD</div>
                    <div class="price-old">6000.0 DZD</div>
                    <div class="price-current">4500.0 DZD</div>
                    <a href="#cta" class="btn pulse">اشتري الآن</a>
                </div>
            </div>
        </section>
        
        <section class="section guarantee" id="guarantee">
            <div class="container">
                <div class="guarantee-content">
                    <h2>ضمان الجودة</h2>
                    <ul class="guarantee-list">
                        <li class="guarantee-item">ضمان رضا العميل 100%</li>
                        <li class="guarantee-item">تجربة خالية من المخاطر واسترجاع فوري للمبلغ <img src="https://example.com/product-image.jpg" alt="A mint green ENZO straightening brush lies horizontally with black bristles, gold trim, a digital display, and control buttons. It has a power cord and rests on a transparent stand. Sleek design suitable for modern hair styling."></li>
                    </ul>
                </div>
            </div>
        </section>
        
        <section class="section faq" id="faq">
            <div class="container">
                <h2>الأسئلة الشائعة</h2>
                <div class="faq-list">
                    <div class="faq-item">
                        <div class="faq-question">كيف تستخدم Brosse Lissante ENZO EN-4102.1؟</div>
                        <div class="faq-answer">عملية الاستخدام بسيطة جداً؛ مرريها بسلاسة على شعرك المبلل أو الجاف لتحصلي على نتائج فورية وناعمة. <img src="https://example.com/product-image.jpg" alt="ENZO straight hair comb with mint green body, gold accents, black bristles, and a digital display. Includes three control buttons and rotating power cord. Reaches 988°F. Box shows branding and 'Intelligent Power Technology' for fast, consistent styling."></div>
                    </div>
                    <div class="faq-item">
                        <div class="faq-question">هل تناسب Brosse Lissante ENZO EN-4102.1 جميع أنواع الشعر؟</div>
                        <div class="faq-answer">بالتأكيد، فهي مثالية لمعظم أنواع الشعر بفضل تقنيتها المتطورة التي تحافظ على صحة ولمعان شعرك.</div>
                    </div>
                </div>
            </div>
        </section>
        
        <section class="section final-cta" id="cta">
            <div class="container">
                <h2>احصلي على إطلالة صالون في منزلك الآن! <img src="https://example.com/product-image.jpg" alt="Ad shows woman with sleek brown hair next to mint green ENZO comb with display, buttons, and gold-tipped bristles. Labeled 'ADVANCED STRAIGHT HAIR COMB' and 'UP TO 988F.' Presents as a high-performance, professional styling tool."></h2>
                <a href="#" class="btn pulse">اشتري الآن</a>
            </div>
        </section>
        
        <footer>
            <div class="container">
                <p>© 2025 ENZO. جميع الحقوق محفوظة.</p>
            </div>
        </footer>
        
        <script>
            // Reveal sections on scroll
            document.addEventListener('DOMContentLoaded', function() {
                const sections = document.querySelectorAll('.section');
                
                // Initially check which sections are visible
                checkSections();
                
                // Check on scroll
                window.addEventListener('scroll', checkSections);
                
                function checkSections() {
                    const triggerBottom = window.innerHeight * 0.8;
                    
                    sections.forEach(section => {
                        const sectionTop = section.getBoundingClientRect().top;
                        
                        if(sectionTop < triggerBottom) {
                            section.classList.add('visible');
                        }
                    });
                }
                
                // FAQ Accordion
                const faqQuestions = document.querySelectorAll('.faq-question');
                
                faqQuestions.forEach(question => {
                    question.addEventListener('click', () => {
                        const answer = question.nextElementSibling;
                        
                        // Toggle active class on question
                        question.classList.toggle('active');
                        
                        // Toggle visibility of answer
                        answer.classList.toggle('visible');
                    });
                });
                
                // Show first FAQ answer by default
                if(faqQuestions.length > 0) {
                    faqQuestions[0].classList.add('active');
                    faqQuestions[0].nextElementSibling.classList.add('visible');
                }
            });
            </script>
        </body>
        </html>
        """