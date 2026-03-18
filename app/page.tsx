import Link from 'next/link';
import Image from 'next/image';
import styles from './page.module.css';

const catBreeds = [
  {
    id: 'bengal',
    name: 'Bengal',
    slug: 'bengal',
    description: 'Pisica Bengal este o rasă hibridă fascinantă, rezultată din încrucișarea pisicilor domestice cu pisici leopard asiatice.',
    origin: 'Statele Unite',
    image: 'https://images.unsplash.com/photo-1606214174585-fe31582dc6ee?w=800',
  },
  {
    id: 'siamese',
    name: 'Siameză',
    slug: 'siameza',
    description: 'Pisica Siameză este una dintre cele mai vechi și mai recunoscute rase de pisici din lume, originară din Thailanda.',
    origin: 'Thailanda',
    image: 'https://images.unsplash.com/photo-1513245543132-31f507417b26?w=800',
  },
  {
    id: 'maine-coon',
    name: 'Maine Coon',
    slug: 'maine-coon',
    description: 'Maine Coon este una dintre cele mai mari rase de pisici domestice, cunoscută drept "gentle giant" (uriașul blând).',
    origin: 'Maine, SUA',
    image: 'https://images.unsplash.com/photo-1574158622682-e40e69881006?w=800',
  },
];

export default function Home() {
  return (
    <main className={styles.main}>
      <div className={styles.container}>
        <div className={styles.header}>
          <h1 className={styles.title}>🐱 Enciclopedia Raselor de Pisici</h1>
          <p className={styles.subtitle}>
            Descoperă cele mai populare rase de pisici din lume
          </p>
        </div>

        <div className={styles.grid}>
          {catBreeds.map((breed) => (
            <Link key={breed.id} href={`/rase/${breed.slug}`} className={styles.card}>
              <div className={styles.imageContainer}>
                <Image
                  src={breed.image}
                  alt={breed.name}
                  fill
                  style={{ objectFit: 'cover' }}
                  sizes="(max-width: 768px) 100vw, (max-width: 1200px) 50vw, 33vw"
                />
                <h2 className={styles.cardTitle}>{breed.name}</h2>
              </div>

              <div className={styles.cardContent}>
                <div className={styles.origin}>
                  <span>🌍</span>
                  <span>Origine: {breed.origin}</span>
                </div>
                <p className={styles.description}>{breed.description}</p>
                <span className={styles.readMore}>
                  Citește mai mult
                  <span className={styles.arrow}>→</span>
                </span>
              </div>
            </Link>
          ))}
        </div>
      </div>
    </main>
  );
}
