import Image from 'next/image';
import Link from 'next/link';
import styles from '../breed.module.css';

export const metadata = {
  title: 'Maine Coon - Ghid Complet',
  description: 'Tot ce trebuie să știi despre pisica Maine Coon: caracteristici, temperament, îngrijire',
};

export default function MaineCoonPage() {
  return (
    <main className={styles.main}>
      <div className={styles.container}>
        <Link href="/" className={styles.backLink}>
          ← Înapoi la toate rasele
        </Link>

        <div className={styles.grid}>
          <div className={styles.imageContainer}>
            <Image
              src="https://images.unsplash.com/photo-1574158622682-e40e69881006"
              alt="Pisică Maine Coon"
              fill
              style={{ objectFit: 'cover' }}
              priority
              sizes="(max-width: 1024px) 100vw, 50vw"
            />
          </div>

          <div>
            <h1 className={styles.title}>Maine Coon</h1>
            
            <div className={styles.origin}>
              <span>🌍</span>
              <span>Origine: <strong>Maine, SUA</strong></span>
            </div>

            <p className={styles.description}>
              Maine Coon este una dintre cele mai mari rase de pisici domestice, cunoscută și drept 
              "gentle giant" (uriașul blând). Originară din statul Maine, SUA, această rasă impresionantă 
              se remarcă prin dimensiunile sale masive, blana luxuriantă și caracterul prietenos.
            </p>

            <div className={styles.infoCard}>
              <h3 className={styles.infoTitle}>Informații Rapide</h3>
              <div className={styles.infoGrid}>
                <div className={styles.infoRow}>
                  <span className={styles.infoLabel}>
                    <span>⏱️</span> Speranță de viață
                  </span>
                  <strong>12-15 ani</strong>
                </div>
                <div className={styles.infoRow}>
                  <span className={styles.infoLabel}>
                    <span>⚖️</span> Greutate
                  </span>
                  <strong>5-11 kg</strong>
                </div>
              </div>
            </div>

            <div className={styles.temperament}>
              <h3 className={styles.temperamentTitle}>Temperament</h3>
              <div className={styles.tags}>
                {['Prietenoasă', 'Inteligentă', 'Jucăușă', 'Adaptabilă', 'Blândă'].map((trait) => (
                  <span key={trait} className={`${styles.tag} ${styles.tagGreen}`}>
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
              Maine Coon are blană semi-lungă deasă care necesită periere regulată, de 3-4 ori pe săptămână. 
              În perioada de năpârlire, periere zilnică este recomandată.
            </p>
          </div>

          <div className={styles.careCard}>
            <div className={styles.careIcon}>🏃</div>
            <h3 className={styles.careTitle}>Exercițiu Fizic</h3>
            <p className={styles.careText}>
              Deși pare mare și leneșă, Maine Coon-ul adoră să se joace și să exploreze. 
              Necesită spațiu pentru a se mișca și jocuri moderate zilnice.
            </p>
          </div>

          <div className={styles.careCard}>
            <div className={styles.careIcon}>🏥</div>
            <h3 className={styles.careTitle}>Sănătate</h3>
            <p className={styles.careText}>
              Maine Coon poate fi predispus la cardiomiopatie hipertrofică (HCM) și displazia șoldului. 
              Testări genetice și monitorizarea greutății sunt importante.
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
