/**
 * Free CA Foundation resources directory — every entry fetched or opened in a
 * browser on 12 Nov 2026 before being listed (verification notes per entry
 * are recorded in each `verifiedHow`).
 *
 * Listing rules (plan §3/§4): only content the owner publishes freely
 * themselves — no leaked lectures, no PDF mirrors; freemium platforms appear
 * only for substantial genuinely-free material, with the upsell named in
 * `freeNote`. Nothing is re-hosted, everything is linked.
 *
 * Known trap, kept on the page: the YouTube channel @ICAICATUBE is NOT ICAI.
 * ICAI's official channel is @theicai.
 *
 * Re-verify links when ICAI reshuffles its portal (it does), and refresh
 * educator playlists per attempt — free batches (e.g. PW "Chanakya") are
 * replaced seasonally.
 */

export const freeResources = {
  "lastChecked": "12 Nov 2026",
  "official": [
    {
      "title": "BoS Knowledge Portal (ICAI Board of Studies)",
      "url": "https://boslive.icai.org/",
      "host": "boslive.icai.org",
      "what": "ICAI's student hub: study material, RTPs, MTPs, live-class schedules and announcements for all levels.",
      "papers": [
        "all"
      ],
      "language": "English / Hindi",
      "requiresLogin": false,
      "freeNote": "Most content is public. Live Virtual Class (LVC) login and some MTP downloads need the free student login (ICAI registration no. + date of birth).",
      "verifiedHow": "fetched 12 Nov 2026; login form fields (Registration No., Date of Birth) seen in page source"
    },
    {
      "title": "Foundation study material (New Scheme), paper-wise",
      "url": "https://boslive.icai.org/education_content_study_material_new_scheme.php?c=foundation",
      "host": "boslive.icai.org",
      "what": "Official ICAI modules for all four papers, chapter-wise PDFs. This is the syllabus reference every exam question is set from.",
      "papers": [
        "all"
      ],
      "language": "English / Hindi",
      "requiresLogin": false,
      "freeNote": "Free to read and download. Printed copies come via the CDS portal (free with registration coupon, otherwise paid).",
      "verifiedHow": "fetched 12 Nov 2026; page lists Paper-1 Accounting, Paper-2 Business Laws, Paper-3 Quantitative Aptitude, Paper-4 Business Economics"
    },
    {
      "title": "Revision Test Papers (RTP), Foundation",
      "url": "https://boslive.icai.org/education_content_rtp.php?c=Foundation",
      "host": "boslive.icai.org",
      "what": "ICAI's per-attempt revision papers with answers, covering every attempt from June 2024 to January 2027, plus Hindi-medium sets.",
      "papers": [
        "all"
      ],
      "language": "English / Hindi",
      "requiresLogin": false,
      "freeNote": "Direct PDF downloads, no login needed. A January 2027 paper PDF returned HTTP 200 application/pdf.",
      "verifiedHow": "fetched 12 Nov 2026; Jan 2027 list page links P1-P4 PDFs on resource.cdn.icai.org"
    },
    {
      "title": "ICAI Mock Test Papers (MTP)",
      "url": "https://boslive.icai.org/education_content.php?p=Mock%20Test%20Papers",
      "host": "boslive.icai.org",
      "what": "ICAI's own Series I and II mock papers with answers for each attempt. This is the gold standard for practice.",
      "papers": [
        "all"
      ],
      "language": "English / Hindi",
      "requiresLogin": true,
      "freeNote": "Free. Some recent series are direct PDFs (e.g. Foundation MTP Series Sep 2025 on resource.cdn.icai.org); older Q&A sets say 'Login ICAI BOS App or BOS Knowledge Portal' (registration no. + DOB). ICAI branches also run physical mock tests; register via the page.",
      "verifiedHow": "fetched 12 Nov 2026; Foundation MTP entries for June 2023, June 2024, Sep 2024, Sep 2025 seen"
    },
    {
      "title": "Past question papers, Foundation (New Scheme)",
      "url": "https://www.icai.org/post/question-papers-foundation-course",
      "host": "icai.org",
      "what": "Official question papers for each attempt from June 2024 to September 2026, plus Hindi-medium papers.",
      "papers": [
        "all"
      ],
      "language": "English / Hindi",
      "requiresLogin": false,
      "verifiedHow": "fetched 12 Nov 2026; sessions June 2024 to September 2026 listed"
    },
    {
      "title": "Suggested answers, Foundation (New Scheme)",
      "url": "https://www.icai.org/post/suggested-answer-foundation-course",
      "host": "icai.org",
      "what": "ICAI's official model answers for each attempt from January 2025 to September 2026. Use them to check how answers are expected to be written.",
      "papers": [
        "all"
      ],
      "language": "English / Hindi",
      "requiresLogin": false,
      "freeNote": "The older https://www.icai.org/post/suggested-answers page only has pre-2010 material. Use this page instead.",
      "verifiedHow": "fetched 12 Nov 2026; linked from boslive Suggested Answers page; sessions Jan 2025 to Sep 2026 listed"
    },
    {
      "title": "Foundation live class schedule (BoS LVC)",
      "url": "https://boslive.icai.org/schedule.php?course=foundation",
      "host": "boslive.icai.org",
      "what": "Timetable of ICAI's free live virtual classes for the current Foundation batch (January 2027 attempt).",
      "papers": [
        "all"
      ],
      "language": "English / Hindi",
      "requiresLogin": false,
      "freeNote": "The schedule is public. Joining live needs the free student login. Recordings are on the ICAI CA Tube YouTube channel.",
      "verifiedHow": "fetched 12 Nov 2026; shows 'Foundation Schedule', Jan 2027 batch"
    },
    {
      "title": "ICAI BOS mobile app (Android)",
      "url": "https://play.google.com/store/apps/details?id=com.macv.icai",
      "host": "play.google.com",
      "what": "ICAI's official app for study material, live and recorded classes, MTPs and MCQs.",
      "papers": [
        "all"
      ],
      "language": "English / Hindi",
      "requiresLogin": true,
      "freeNote": "Free. Uses the student login.",
      "verifiedHow": "fetched 12 Nov 2026; og:title 'ICAI BOS - Apps on Google Play'; package com.macv.icai confirmed by web search (ICAI announcement pages)"
    },
    {
      "title": "ICAI BOS app (iPhone)",
      "url": "https://apps.apple.com/in/app/icai-bos/id1580286245",
      "host": "apps.apple.com",
      "what": "The iOS version of the official BoS app.",
      "papers": [
        "all"
      ],
      "language": "English / Hindi",
      "requiresLogin": true,
      "verifiedHow": "fetched 12 Nov 2026; title 'ICAI BOS App - App Store'"
    },
    {
      "title": "SSP (Self Service Portal): registration, exam forms, admit card",
      "url": "https://eservices.icai.org/",
      "host": "eservices.icai.org",
      "what": "Where students register for Foundation, fill exam forms and download admit cards.",
      "papers": [
        "all"
      ],
      "language": "English",
      "requiresLogin": true,
      "verifiedHow": "fetched 12 Nov 2026; redirects to 'SSP Login' page"
    },
    {
      "title": "ICAI results portal",
      "url": "https://icai.nic.in/",
      "host": "icai.nic.in",
      "what": "Official results and merit lists for the Foundation exam.",
      "papers": [
        "all"
      ],
      "language": "English",
      "requiresLogin": false,
      "freeNote": "Checking a result needs your roll number. The page itself is public.",
      "verifiedHow": "exa fetch 12 Nov 2026 (curl timed out); page 'ICAI Exam Results' listing Foundation results"
    },
    {
      "title": "CDS portal (printed ICAI study material)",
      "url": "https://cds.icai.org/",
      "host": "cds.icai.org",
      "what": "ICAI's portal for ordering printed modules. Registered students redeem a free coupon; anyone else can buy them at ICAI prices.",
      "papers": [
        "all"
      ],
      "language": "English / Hindi",
      "requiresLogin": true,
      "freeNote": "Foundation registration includes one free coupon for the printed kit, valid for 1 year (per ICAI FAQ).",
      "verifiedHow": "fetched 12 Nov 2026 (HTTP 200, 'ICAI CDS PORTAL'); coupon rules from ICAI Call Sahayata FAQ PDF"
    }
  ],
  "youtube": [
    {
      "title": "ICAI CA Tube (official ICAI channel)",
      "url": "https://www.youtube.com/@theicai",
      "host": "youtube.com",
      "what": "ICAI's own channel, with full recordings of BoS live virtual classes taught by ICAI faculty for all four papers, one playlist per attempt.",
      "papers": [
        "all"
      ],
      "language": "English with Hindi (Hinglish classroom style)",
      "requiresLogin": false,
      "freeNote": "Entirely free. Warning: @ICAICATUBE is a different, unofficial channel. Use @theicai, which is the channel boslive.icai.org links to as youtube.com/user/icaiorgtube.",
      "verifiedHow": "fetched 12 Nov 2026; channelId UCMBsmDfLTOPRicJISPeXacw, vanity @theicai, linked from boslive footer",
      "playlists": [
        {
          "label": "Foundation Live Virtual Classes, January 2027 exams",
          "url": "https://www.youtube.com/playlist?list=PLXenx517iUZo",
          "papers": [
            "all"
          ],
          "what": "The current batch of ICAI live classes, chapter by chapter, with sessions for all four papers."
        },
        {
          "label": "Foundation Live Virtual Classes, September 2026 exams",
          "url": "https://www.youtube.com/playlist?list=PLP0oTm4FOBFJGaIjLVUNVlwkPLYJOGCR4",
          "papers": [
            "all"
          ],
          "what": "The previous batch, already complete across all four papers. Useful if you want to binge rather than wait for the live batch."
        },
        {
          "label": "Foundation 'Success at CA Exam' Series I & II, September 2026",
          "url": "https://www.youtube.com/playlist?list=PLSFfiExDKShc",
          "papers": [
            "all"
          ],
          "what": "ICAI's own exam-orientation and MTP-discussion sessions for the September 2026 attempt."
        }
      ]
    },
    {
      "title": "CA Wallah by PW (Physics Wallah)",
      "url": "https://www.youtube.com/@cawallahbypw",
      "host": "youtube.com",
      "what": "PW's CA channel. Its free 'Chanakya 4.0' Foundation batch runs on YouTube with one long lecture per chapter for each paper, plus marathons and revision series.",
      "papers": [
        "all"
      ],
      "language": "Hindi / Hinglish",
      "requiresLogin": false,
      "freeNote": "Chanakya 4.0 lectures are free on YouTube. Notes, DPPs and mock tests for the batch are on the PW app/site (free account). 'Sampurna' batches are paid, and YouTube only has their demo lectures.",
      "verifiedHow": "fetched channel + playlists 12 Nov 2026; Chanakya 4.0 described as free on pw.live article dated 12 Jun 2026",
      "playlists": [
        {
          "label": "Accounting, Free Chanakya 4.0",
          "url": "https://www.youtube.com/playlist?list=PLMVLFT2PTutg",
          "papers": [
            "accounting"
          ],
          "what": "Chapter-wise one-shot Accounting lectures (CA Manish Mahajan, CA Nitin Goel). The playlist is still being added to."
        },
        {
          "label": "Business Laws, Free Chanakya 4.0",
          "url": "https://www.youtube.com/playlist?list=PLWVV1A75kqQM",
          "papers": [
            "business-laws"
          ],
          "what": "Chapter-wise Business Laws lectures (CA Nikesh Agrawal, CA Chaitanya Jain)."
        },
        {
          "label": "Quantitative Aptitude, Free Chanakya 4.0",
          "url": "https://www.youtube.com/playlist?list=PLHrItINKQiVM",
          "papers": [
            "quantitative-aptitude"
          ],
          "what": "Chapter-wise QA lectures (Anurag Chauhan, Ashish Bhatia)."
        },
        {
          "label": "Business Economics, Free Chanakya 4.0",
          "url": "https://www.youtube.com/playlist?list=PLLhh85hSLazM",
          "papers": [
            "business-economics"
          ],
          "what": "Chapter-wise Economics lectures (Love Kaushik)."
        }
      ]
    },
    {
      "title": "CA Foundation Grooming Education (Chandan Poddar)",
      "url": "https://www.youtube.com/@CAFoundationGroomingEducation",
      "host": "youtube.com",
      "what": "A Foundation-only channel with full-course playlists for each paper labelled for the Jan/May/Sep 2026 attempts, plus law answer-writing practice and ICAI MTP walkthroughs.",
      "papers": [
        "all"
      ],
      "language": "Hindi / Hinglish (from titles; audio not checked)",
      "requiresLogin": false,
      "freeNote": "Playlists are free. Grooming Education also sells courses.",
      "verifiedHow": "fetched channel playlists 12 Nov 2026; also recommended unprompted in an r/CharteredAccountants thread (May 2026)",
      "playlists": [
        {
          "label": "Accounts, Jan/May/Sep 2026",
          "url": "https://www.youtube.com/playlist?list=PLVEE42ag3kS8XFbN_E-nfsjE25TV9U19u",
          "papers": [
            "accounting"
          ],
          "what": "Complete-chapter Accounting lectures, uploaded roughly 10 to 12 months ago."
        },
        {
          "label": "Law, Jan/May/Sep 2026",
          "url": "https://www.youtube.com/playlist?list=PLVEE42ag3kS93BmJjbZMMOUGX1FkkmxUB",
          "papers": [
            "business-laws"
          ],
          "what": "Business Laws course lectures. Pair it with the law answer-writing practice playlists on the same channel."
        },
        {
          "label": "Quantitative Aptitude, Jan/May/Sep 2026",
          "url": "https://www.youtube.com/playlist?list=PLVEE42ag3kS8nUySgojIcGuoBcuRPTDmE",
          "papers": [
            "quantitative-aptitude"
          ],
          "what": "QA (maths, statistics, logical reasoning) course lectures."
        },
        {
          "label": "Economics, Jan/May/Sep 2026",
          "url": "https://www.youtube.com/playlist?list=PLVEE42ag3kS9-K3Nitui13_5TCm7blPU2",
          "papers": [
            "business-economics"
          ],
          "what": "Business Economics course lectures."
        }
      ]
    },
    {
      "title": "CA Hardik Manchanda",
      "url": "https://www.youtube.com/@cahardikmanchanda",
      "host": "youtube.com",
      "what": "Strong on Accounts and Economics: chapter one-shots with ICAI questions, RTP and PYQ solving, and per-attempt revision playlists.",
      "papers": [
        "accounting",
        "business-economics"
      ],
      "language": "Hinglish",
      "requiresLogin": false,
      "freeNote": "The YouTube one-shots are free. The channel links to his paid courses.",
      "verifiedHow": "fetched channel playlists 12 Nov 2026",
      "playlists": [
        {
          "label": "Accounts ONE SHOT",
          "url": "https://www.youtube.com/playlist?list=PLuPsXhXyb-c82TOFxpHiq-9pw4i7ybB6m",
          "papers": [
            "accounting"
          ],
          "what": "Chapter one-shots for Accounting, best used for revision after a full course."
        },
        {
          "label": "Business Economics (ONE SHOT, new syllabus)",
          "url": "https://www.youtube.com/playlist?list=PLuPsXhXyb-c-Lher7vrJInHHrR_mGHIqT",
          "papers": [
            "business-economics"
          ],
          "what": "One-shot Economics chapters with ICAI illustrations (National Income, Money Demand and others), streamed about 2 years ago for the new scheme."
        }
      ]
    }
  ],
  "bareActs": [
    {
      "title": "The Indian Contract Act, 1872 (India Code)",
      "url": "https://www.indiacode.nic.in/handle/123456789/2187",
      "host": "indiacode.nic.in",
      "what": "The official bare act text, section by section. Use it to read the exact wording of sections the module quotes.",
      "papers": [
        "business-laws"
      ],
      "language": "English",
      "requiresLogin": false,
      "verifiedHow": "exa fetch 12 Nov 2026 (curl timed out); Act ID 187209"
    },
    {
      "title": "The Sale of Goods Act, 1930 (India Code)",
      "url": "https://www.indiacode.nic.in/handle/123456789/2390",
      "host": "indiacode.nic.in",
      "what": "Official bare act text.",
      "papers": [
        "business-laws"
      ],
      "language": "English",
      "requiresLogin": false,
      "verifiedHow": "exa fetch 12 Nov 2026; Act ID 193003"
    },
    {
      "title": "The Indian Partnership Act, 1932 (India Code)",
      "url": "https://www.indiacode.nic.in/handle/123456789/2394",
      "host": "indiacode.nic.in",
      "what": "Official bare act text.",
      "papers": [
        "business-laws"
      ],
      "language": "English",
      "requiresLogin": false,
      "verifiedHow": "exa search 12 Nov 2026 returned full page content (Act ID 193209); live fetch timed out (India Code is slow); same Act also seen in India Code browse listing"
    },
    {
      "title": "The Limited Liability Partnership Act, 2008 (India Code)",
      "url": "https://www.indiacode.nic.in/handle/123456789/2023",
      "host": "indiacode.nic.in",
      "what": "Official bare act text.",
      "papers": [
        "business-laws"
      ],
      "language": "English",
      "requiresLogin": false,
      "verifiedHow": "exa fetch 12 Nov 2026; Act ID 200906"
    },
    {
      "title": "The Companies Act, 2013 (India Code)",
      "url": "https://www.indiacode.nic.in/handle/123456789/2114",
      "host": "indiacode.nic.in",
      "what": "Official bare act text. Foundation covers only the basics (Chapter 6 of the module), so read selectively.",
      "papers": [
        "business-laws"
      ],
      "language": "English",
      "requiresLogin": false,
      "verifiedHow": "exa fetch 12 Nov 2026; Act ID 201318"
    },
    {
      "title": "The Negotiable Instruments Act, 1881 (India Code)",
      "url": "https://www.indiacode.nic.in/handle/123456789/2189",
      "host": "indiacode.nic.in",
      "what": "Official bare act text.",
      "papers": [
        "business-laws"
      ],
      "language": "English",
      "requiresLogin": false,
      "verifiedHow": "exa fetch 12 Nov 2026; Act ID 188126"
    },
    {
      "title": "MCA e-book: Acts (Companies Act 2013, LLP Act 2008)",
      "url": "https://www.mca.gov.in/content/mca/global/en/acts-rules/ebooks/acts.html",
      "host": "mca.gov.in",
      "what": "The Ministry of Corporate Affairs' searchable e-book of the Acts it administers, kept up to date with amendments.",
      "papers": [
        "business-laws"
      ],
      "language": "English / Hindi",
      "requiresLogin": false,
      "freeNote": "The page blocks scripts and bots (curl gets 403) but loads normally in a browser.",
      "verifiedHow": "loaded in Chrome 12 Nov 2026; page 'Acts', 'Last Updated: 11 November, 2026'"
    }
  ],
  "background": [
    {
      "title": "Khan Academy: Statistics and probability",
      "url": "https://www.khanacademy.org/math/statistics-probability",
      "host": "khanacademy.org",
      "what": "Free background practice for the QA statistics chapters (central tendency, dispersion, probability, distributions, correlation). It goes deeper than Foundation needs, so pick units.",
      "papers": [
        "quantitative-aptitude"
      ],
      "language": "English (Hindi available on some Khan content)",
      "requiresLogin": false,
      "freeNote": "Completely free (non-profit). An account is optional and only for tracking progress.",
      "verifiedHow": "loaded in Chrome 12 Nov 2026; 'Statistics and probability, 16 UNITS'"
    },
    {
      "title": "Khan Academy: Microeconomics",
      "url": "https://www.khanacademy.org/economics-finance-domain/microeconomics",
      "host": "khanacademy.org",
      "what": "Intuition for demand, supply, elasticity, consumer behaviour, production and cost, and market forms. These map to BE chapters 2 to 4.",
      "papers": [
        "business-economics"
      ],
      "language": "English",
      "requiresLogin": false,
      "verifiedHow": "loaded in Chrome 12 Nov 2026; 'Microeconomics, 9 UNITS'"
    },
    {
      "title": "Khan Academy: Macroeconomics",
      "url": "https://www.khanacademy.org/economics-finance-domain/macroeconomics",
      "host": "khanacademy.org",
      "what": "Background for national income, money, fiscal and monetary policy, and international trade. These map to BE chapters 6 to 10. The examples are US-centred, so use the ICAI module for Indian specifics.",
      "papers": [
        "business-economics"
      ],
      "language": "English",
      "requiresLogin": false,
      "verifiedHow": "loaded in Chrome 12 Nov 2026; 'Macroeconomics, 8 UNITS'"
    }
  ],
  "communities": [
    {
      "title": "r/CharteredAccountants",
      "url": "https://www.reddit.com/r/CharteredAccountants/",
      "host": "reddit.com",
      "what": "India's main CA subreddit. Foundation students regularly post doubts, ask for faculty recommendations and share exam experiences.",
      "papers": [
        "all"
      ],
      "language": "English / Hinglish",
      "requiresLogin": false,
      "freeNote": "Read without an account; posting needs a Reddit account. The rules ban unofficial WhatsApp/Telegram groups and route exam talk into designated exam threads.",
      "verifiedHow": "exa fetch 12 Nov 2026 (Nov 2026 exam thread pinned, created 2016); Foundation doubt posts dated Jan, Apr, May, Jun and Jul 2026 found via search"
    },
    {
      "title": "CAclubindia: Students forum",
      "url": "https://www.caclubindia.com/forum/display.asp?cat_id=8",
      "host": "caclubindia.com",
      "what": "A long-running Indian CA forum. The Students section covers exam doubts, ICAI announcements and paper discussions.",
      "papers": [
        "all"
      ],
      "language": "English",
      "requiresLogin": false,
      "freeNote": "Free. Posting needs a free account. The site also runs paid courses and ads.",
      "verifiedHow": "fetched 12 Nov 2026; 'Students Discussion' with posts dated 7 to 11 Nov 2026"
    },
    {
      "title": "ICAI official Telegram channel",
      "url": "https://t.me/theicai",
      "host": "t.me",
      "what": "ICAI's official broadcast channel for announcements (not a discussion group), linked from the boslive.icai.org footer.",
      "papers": [
        "all"
      ],
      "language": "English",
      "requiresLogin": false,
      "verifiedHow": "exa fetch 12 Nov 2026 ('The Institute of Chartered Accountants of India, ICAI' verified channel); linked from boslive footer"
    }
  ]
};
