-- BorsaRadar veritabanı şeması
-- MySQL 8.0+, UTF8MB4

CREATE DATABASE IF NOT EXISTS borsaradar
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE borsaradar;

-- ─────────────────────────────────────────────
-- 1. Hisse fiyatları
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS hisse_fiyatlari (
    id                BIGINT          NOT NULL AUTO_INCREMENT,
    ticker            VARCHAR(10)     NOT NULL,
    fiyat             DECIMAL(12, 4),
    degisim_yuzde     DECIMAL(8, 4),
    hacim             BIGINT,
    guncelleme_zamani DATETIME(3),
    veri_kaynagi      ENUM('borsapy', 'yfinance', 'cache'),

    PRIMARY KEY (id),
    INDEX idx_hisse_ticker_zaman (ticker, guncelleme_zamani)
) ENGINE = InnoDB
  DEFAULT CHARSET = utf8mb4
  COLLATE = utf8mb4_unicode_ci;

-- ─────────────────────────────────────────────
-- 2. Haberler
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS haberler (
    id               BIGINT          NOT NULL AUTO_INCREMENT,
    baslik           TEXT            NOT NULL,
    url              VARCHAR(512),
    kaynak           VARCHAR(100),
    yayin_zamani     DATETIME,
    sentiment        ENUM('pozitif', 'negatif', 'notr') NOT NULL DEFAULT 'notr',
    sentiment_skoru  DECIMAL(5, 4),
    etki_skoru       TINYINT                            NOT NULL DEFAULT 0,
    url_hash         CHAR(64),

    PRIMARY KEY (id),
    UNIQUE KEY uq_haberler_url_hash (url_hash),
    INDEX idx_haberler_yayin_zamani (yayin_zamani)
) ENGINE = InnoDB
  DEFAULT CHARSET = utf8mb4
  COLLATE = utf8mb4_unicode_ci;

-- ─────────────────────────────────────────────
-- 3. Haber–varlık eşleşme
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS haber_varlik_eslesme (
    haber_id          BIGINT       NOT NULL,
    varlik_turu       ENUM('hisse', 'maden', 'doviz') NOT NULL,
    varlik_kodu       VARCHAR(20)  NOT NULL,
    eslestirme_yontemi ENUM('ner', 'sektor', 'keyword') NOT NULL,

    PRIMARY KEY (haber_id, varlik_kodu),
    CONSTRAINT fk_hve_haber
        FOREIGN KEY (haber_id) REFERENCES haberler (id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
) ENGINE = InnoDB
  DEFAULT CHARSET = utf8mb4
  COLLATE = utf8mb4_unicode_ci;

-- ─────────────────────────────────────────────
-- 4. Maden fiyatları
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS maden_fiyatlari (
    id                BIGINT          NOT NULL AUTO_INCREMENT,
    maden_kodu        VARCHAR(10)     NOT NULL,
    fiyat_usd         DECIMAL(12, 4),
    fiyat_try         DECIMAL(12, 4),
    guncelleme_zamani DATETIME(3),

    PRIMARY KEY (id),
    INDEX idx_maden_kodu_zaman (maden_kodu, guncelleme_zamani)
) ENGINE = InnoDB
  DEFAULT CHARSET = utf8mb4
  COLLATE = utf8mb4_unicode_ci;

-- ─────────────────────────────────────────────
-- 5. API sağlık durumu
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS api_saglik (
    api_adi               VARCHAR(50)                          NOT NULL,
    son_basari_zamani     DATETIME,
    son_hata_zamani       DATETIME,
    son_hata_mesaji       TEXT,
    ardisik_hata_sayisi   INT                                  NOT NULL DEFAULT 0,
    durum                 ENUM('normal', 'degraded', 'down')   NOT NULL DEFAULT 'normal',

    PRIMARY KEY (api_adi)
) ENGINE = InnoDB
  DEFAULT CHARSET = utf8mb4
  COLLATE = utf8mb4_unicode_ci;
