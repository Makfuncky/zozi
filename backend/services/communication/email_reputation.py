"""Email domain reputation service for fraud detection.

Checks email addresses against known disposable/temporary domains,
role-based aliases (catch-all), and suspicious TLDs.
"""

from __future__ import annotations

import logging
import re
from typing import Optional

logger = logging.getLogger(__name__)


# Known disposable email domains (comprehensive list)
DISPOSABLE_DOMAINS: set[str] = {
    "mailinator.com", "guerrillamail.com", "tempmail.com", "10minutemail.com",
    "throwaway.email", "yopmail.com", "getairmail.com", "fakeinbox.com",
    "sharklasers.com", "trashmail.com", "trashmail.me", "spamgourmet.com",
    "mailcatch.com", "mailexpire.com", "mytrashmail.com", "temp-mail.org",
    "tempemail.net", "emailondeck.com", "mailsac.com", "inboxbear.com",
    "receive-smss.com", "dispostable.com", "burnermail.io", "mohmal.com",
    "mailmetrash.com", "filzmail.com", "mailnator.com", "mail-temp.com",
    "tempinbox.com", "throwaway.io", "jetable.org", "lroid.com",
    "incognitomail.com", "mailmoat.com", "maileater.com", "mailinator2.com",
    "spambox.us", "wh4f.org", "guerrillamail.org", "guerrillamail.biz",
    "guerrillamail.net", "guerrillamail.de", "deadaddress.com",
    "discard.email", "e4ward.com", "emailabc.com", "emailias.com",
    "emailinfive.com", "emaildrop.io", "fakemailgenerator.com",
    "fammail.com", "gigacoco.com", "greatmail.com", "haltospam.com",
    "hotpop.com", "inboxalias.com", "ipoo.org", "kulturbetrieb.info",
    "luxuryalcoholic.com", "mail-temporaire.fr", "mail1a.de",
    "mail434.com", "mailbiz.biz", "mailbucket.org", "maildu.de",
    "mailentry.com", "mailfence.com", "mailhaven.com", "mailhex.com",
    "mailhood.com", "mailimate.com", "mailin8r.com", "mailinator.net",
    "mailismagic.com", "mailme.ir", "mailmetrash.com", "mailmoat.com",
    "mailnator.com", "mailnesia.com", "mailnull.com", "mailpoof.com",
    "mailproxsy.com", "mailquack.com", "mailsac.com", "mailseal.de",
    "mailshiv.com", "mailsiphon.com", "mailslapping.com", "mailsnails.com",
    "mailtothis.com", "mailtraps.com", "mailvia.com", "mailzilla.com",
    "mymailoasis.com", "nepwk.com", "nowmymail.com", "oneoffmail.com",
    "oopi.org", "pookmail.com", "proxymail.eu", "prtnx.com",
    "punkass.com", "quickinbox.com", "rcpt.at", "recode.me",
    "rhyta.com", "sneakemail.com", "sofimail.com", "sofort-mail.de",
    "sogetthis.com", "spam.la", "spam4.me", "spamavert.com",
    "spambob.com", "spambob.net", "spambob.org", "spamex.com",
    "spamfree24.org", "spamgourmet.com", "spamhole.com", "spamkill.info",
    "spamsalad.com", "spamserver.de", "spamthe.net", "spamthis.co.uk",
    "spamtraffic.com", "tempail.com", "tempemail.com", "tempmail.co",
    "tempmail.de", "tempmail.eu", "tempmail.it", "tempmail.net",
    "tempmail.org", "tempmail.us", "tempomail.fr", "temporaryforwarding.com",
    "temporaryinbox.com", "thankyou2010.com", "thc.st", "theguillotine.com",
    "throwaway.email", "throwaway.de", "tmpeml.com", "tmpmail.net",
    "trash2009.com", "trashdevil.de", "trashmail.at", "trashmail.com",
    "trashmail.de", "trashmail.me", "trashmail.net", "trashmail.org",
    "trashmail.ws", "trashymail.com", "trashymail.net", "turual.com",
    "tyldd.com", "uggsrock.com", "wegwerfmail.de", "wegwerfmail.net",
    "wegwerfmail.org", "wh4f.org", "whyspam.me", "willselfdestruct.com",
    "winemaven.info", "wronghead.com", "wuzup.net", "xagloo.com",
    "xemaps.com", "xents.com", "xmaily.com", "xoxy.net", "yep.it",
    "yopmail.com", "yopmail.fr", "yopmail.net", "yuurok.com",
    "zehnminutenmail.de", "zippymail.info", "zoaxe.com", "zoemail.org",
    "emailsy.info", "mailmetrash.com", "hulapla.de", "binkmail.com",
    "bobmail.info", "chacuo.net", "cool.fr.nf", "correo.blogos.net",
    "crapmail.org", "cuvox.de", "dandikmail.com", "dayrep.com",
    "dicksinhisan.us", "dicksinmyan.us", "deadaddress.com",
    "dodgeit.com", "dodgit.com", "dodgit.org", "drdrb.net",
    "dumpyemail.com", "eelmail.com", "einmalmail.de", "einrot.com",
    "eintagsmail.de", "email-fake.com", "emailgo.de", "emaillime.com",
    "emailmiser.com", "emailsensei.com", "emailtemporario.com.br",
    "emailto.de", "emailwarden.com", "ephemail.net", "explodemail.com",
    "fake-mail.net", "fakemail.fr", "fakemailgenerator.com",
    "fakemailz.com", "fammail.com", "fanswap.com", "firstinbox.net",
    "flagsonline.net", "fizmail.com", "frapmail.com", "front14.org",
    "fuckingduh.com", "fudgerub.com", "garliclife.com", "get2mail.fr",
    "getnada.com", "gishpuppy.com", "glitch.sx", "gmial.com", "goemailgo.com",
    "gurumail.net", "harry.lu", "hatespam.org", "herp.in", "hidemyass.com",
    "hotmai.com", "hotmial.com", "ieatspam.eu", "ieatspam.info",
    "ihateyoualot.info", "imails.info", "inbaking.in", "inbox.si",
    "inboxalias.com", "inboxclean.com", "inboxclean.org", "inboxstore.me",
    "inkynigeria.net", "ip6.li", "irish2me.com", "jadopado.com",
    "japanyn.net", "jetable.com", "jetable.net", "jetable.org",
    "junk.to", "junk1e.com", "kasmail.com", "kaspop.com", "kcrw.de",
    "keepmymail.com", "killmail.com", "killmail.net", "kir.ch.tc",
    "klassmaster.com", "klassmaster.net", "klzlk.com", "kulturbetrieb.info",
    "letterboxes.org", "linuxmail.so", "litedrop.com", "lom.kr",
    "lookugly.com", "lopl.co.cc", "lr7.us", "lroid.com", "luxuryalcoholic.com",
    "macr2.com", "magicmail.co.kr", "mailexpire.com", "mailin8r.com",
    "mailinatar.com", "mailinater.com", "mailinator.co.uk",
    "mailinator.com", "mailinator.gq", "mailinator.info", "mailinator.net",
    "mailinator.org", "mailinator.us", "mailnator.com", "mailnull.com",
}

# Known role-based/catch-all aliases
ROLE_ALIASES: set[str] = {
    "admin", "support", "info", "contact", "sales", "billing",
    "help", "noreply", "no-reply", "postmaster", "webmaster",
    "abuse", "hostmaster", "marketing", "newsletter", "press",
    "privacy", "security", "unsubscribe", "subscribe", "feedback",
    "notifications", "team", "hello", "mailer-daemon",
}


def check_email_reputation(email: str) -> dict:
    """Check email for fraud indicators.

    Returns a dict with:
    - is_disposable: bool
    - is_role_alias: bool
    - suspicious_tld: bool
    - domain: str
    - risk_level: str (none / low / medium / high)
    """
    if not email or "@" not in email:
        return {
            "is_disposable": False,
            "is_role_alias": False,
            "suspicious_tld": False,
            "domain": "",
            "risk_level": "none",
        }

    parts = email.split("@")
    local_part = parts[0].lower()
    domain = parts[1].lower()

    is_disposable = domain in DISPOSABLE_DOMAINS
    is_role_alias = local_part in ROLE_ALIASES

    suspicious_tlds = {".tk", ".ml", ".ga", ".cf", ".gq"}
    suspicious_tld = any(domain.endswith(tld) for tld in suspicious_tlds)

    if is_disposable:
        risk_level = "high"
    elif suspicious_tld:
        risk_level = "medium"
    elif is_role_alias:
        risk_level = "low"
    else:
        risk_level = "none"

    return {
        "is_disposable": is_disposable,
        "is_role_alias": is_role_alias,
        "suspicious_tld": suspicious_tld,
        "domain": domain,
        "risk_level": risk_level,
    }


def extract_additional_signals_from_user(email: Optional[str], phone: Optional[str]) -> dict:
    """Build additional_signals dict for FraudScoringEngine from user data."""
    signals: dict = {}

    if email:
        rep = check_email_reputation(email)
        signals["disposable_email"] = rep["is_disposable"]
        signals["email_risk_level"] = rep["risk_level"]

    if phone:
        cleaned = re.sub(r"[^0-9+]", "", phone or "")
        is_valid = len(cleaned) >= 7 and len(cleaned) <= 15
        signals["invalid_phone"] = not is_valid

    return signals

