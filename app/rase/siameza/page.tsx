import Image from 'next/image';
import Link from 'next/link';
import styles from '../breed.module.css';

export const metadata = {
  title: 'Siameză - Ghid Complet',
  description: 'Tot ce trebuie să știi despre pisica Siameză: caracteristici, temperament, îngrijire',
};

export default function SiamesePage() {
  return (
    <main className={styles.main}>
      <div className={styles.container}>
        <Link href="/" className={styles.backLink}>
          ← Înapoi la toate rasele
        </Link>

        <div className={styles.grid}>
          <div className={styles.imageContainer}>
            <Image
              src="https://images.unsplash.com/photo-1513245543132-31f507417b26"
              alt="Pisică Siameză"
              fill
              style={{ objectFit: 'cover' }}
              priority
              sizes="(max-width: 1024px) 100vw, 50vw"
            />
          </div>

          <div>
            <h1 className={styles.title}>Siameză</h1>
            
            <div className={styles.origin}>
              <span>🌍</span>
              <span>Origine: <strong>Thailanda (Siam)</strong></span>
            </div>

            <p className={styles.description}>
              Pisica Siameză este una dintre cele mai vechi și mai recunoscute rase de pisici din lume. 
              Originară din Thailanda (fostul Siam), această rasă elegantă se distinge prin corpul său suplu, 
              ochii albaștri strălucitori și coloritul distinctiv "point" pe față, urechi, labe și coadă.
            </p>

            <div className={styles.infoCard}>
              <h3 className={styles.infoTitle}>Informații Rapide</h3>
              <div className={styles.infoGrid}>
                <div className={styles.infoRow}>
                  <span className={styles.infoLabel}>
                    <span>⏱️</span> Speranță de viață
                  </span>
                  <strong>15-20 ani</strong>
                </div>
                <div className={styles.infoRow}>
                  <span className={styles.infoLabel}>
                    <span>⚖️</span> Greutate
                  </span>
                  <strong>3-5 kg</strong>
                </div>
              </div>
            </div>

            <div className={styles.temperament}>
              <h3 className={styles.temperamentTitle}>Temperament</h3>
              <div className={styles.tags}>
                {['Vocală', 'Afectuoasă', 'Inteligentă', 'Socială', 'Loială'].map((trait) => (
                  <span key={trait} className={`${styles.tag} ${styles.tagBlue}`}>
                    {trait}
                  </span>
                ))}
              </div>
            </div>
          </div>
        </div>

        <div className={styles.careGrid}>
          <div className={styles.careCard}>
            <div className={styles.careIcon}>✨</div>
            <h3 className={styles.careTitle}>Îngrijire Blană</h3>
            <p className={styles.careText}>
              Siameza are blană scurtă și fină care necesită îngrijire minimă. O periere săptămânală 
              este suficientă pentru a menține blana strălucitoare.
            </p>
          </div>

          <div className={styles.careCard}>
            <div className={styles.careIcon}>🏃</div>
            <h3 className={styles.careTitle}>Exercițiu Fizic</h3>
            <p className={styles.careText}>
              Deși nu la fel de energică ca Bengal-ul, Siameza este activă și necesită jocuri zilnice. 
              Iubește jocurile interactive cu stăpânul.
            </p>
          </div>

          <div className={styles.careCard}>
            <div className={styles.careIcon}>🏥</div>
            <h3 className={styles.careTitle}>Sănătate</h3>
            <p className={styles.careText}>
              Siameza poate fi predispusă la probleme dentare și astm felin. Igienă dentară regulată 
              și controale veterinare sunt esențiale.
            </p>
          </div>
        </div>

        <div className={styles.ctaContainer}>
          <Link href="/" className={styles.ctaButton}>
            Explorează Alte Rase
          </Link>
        </div>
      </div>
    </main>
  );
}
