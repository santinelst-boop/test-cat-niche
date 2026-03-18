import Image from 'next/image';
import Link from 'next/link';
import styles from '../breed.module.css';

export const metadata = {
  title: 'Bengal - Ghid Complet',
  description: 'Tot ce trebuie să știi despre pisica Bengal: caracteristici, temperament, îngrijire',
};

export default function BengalPage() {
  return (
    <main className={styles.main}>
      <div className={styles.container}>
        <Link href="/" className={styles.backLink}>
          ← Înapoi la toate rasele
        </Link>

        <div className={styles.grid}>
          <div className={styles.imageContainer}>
            <Image
              src="https://images.unsplash.com/photo-1606214174585-fe31582dc6ee"
              alt="Pisică Bengal"
              fill
              style={{ objectFit: 'cover' }}
              priority
              sizes="(max-width: 1024px) 100vw, 50vw"
            />
          </div>

          <div>
            <h1 className={styles.title}>Bengal</h1>
            
            <div className={styles.origin}>
              <span>🌍</span>
              <span>Origine: <strong>Statele Unite</strong></span>
            </div>

            <p className={styles.description}>
              Pisica Bengal este o rasă hibridă fascinantă, rezultată din încrucișarea pisicilor domestice 
              cu pisici leopard asiatice (Prionailurus bengalensis). Această rasă se remarcă prin blana sa 
              strălucitoare cu pete sau marmoreuri distinctive, care îi conferă un aspect sălbatic și exotic.
            </p>

            <div className={styles.infoCard}>
              <h3 className={styles.infoTitle}>Informații Rapide</h3>
              <div className={styles.infoGrid}>
                <div className={styles.infoRow}>
                  <span className={styles.infoLabel}>
                    <span>⏱️</span> Speranță de viață
                  </span>
                  <strong>12-16 ani</strong>
                </div>
                <div className={styles.infoRow}>
                  <span className={styles.infoLabel}>
                    <span>⚖️</span> Greutate
                  </span>
                  <strong>4-7 kg</strong>
                </div>
              </div>
            </div>

            <div className={styles.temperament}>
              <h3 className={styles.temperamentTitle}>Temperament</h3>
              <div className={styles.tags}>
                {['Energică', 'Jucăușă', 'Inteligentă', 'Curioasă', 'Socială'].map((trait) => (
                  <span key={trait} className={`${styles.tag} ${styles.tagOrange}`}>
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
              Bengal-ul are blană scurtă și necesită periere minimă, de 1-2 ori pe săptămână. 
              Blana lor are o textură mătăsoasă unică care nu se încâlcește ușor.
            </p>
          </div>

          <div className={styles.careCard}>
            <div className={styles.careIcon}>🏃</div>
            <h3 className={styles.careTitle}>Exercițiu Fizic</h3>
            <p className={styles.careText}>
              Fiind o rasă foarte activă, Bengal-ul necesită multă stimulare fizică și mentală. 
              Recomandăm jocuri interactive zilnice și jucării puzzle.
            </p>
          </div>

          <div className={styles.careCard}>
            <div className={styles.careIcon}>🏥</div>
            <h3 className={styles.careTitle}>Sănătate</h3>
            <p className={styles.careText}>
              Bengal-ul este în general sănătos, dar poate fi predispus la cardiomiopatie hipertrofică (HCM). 
              Controale veterinare regulate sunt recomandate.
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
