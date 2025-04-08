from playwright.sync_api import Page, expect
import pytest

@pytest.mark.parametrize(
    "date, res_url",
    [
        ("17 March 2020", "https://www.gov.uk/government/speeches/prime-ministers-address-to-the-nation-4-january-2021"),
        ("21 March 2020", "https://www.gov.uk/government/speeches/prime-ministers-statement-on-coronavirus-covid-19-22-september-2020"),
        ("23 March 2020", "https://www.gov.uk/government/news/pm-confirms-schools-colleges-and-nurseries-on-track-to-begin-phased-reopening"),
        ("24 March 2020", "https://www.gov.uk/government/speeches/pm-statement-on-coronavirus-16-march-2020"),
        ("11 May 2020", "https://www.gov.uk/government/news/schools-colleges-and-early-years-settings-to-close"),
        ("01 June 2020", "https://www.gov.uk/government/speeches/pm-address-to-the-nation-on-coronavirus-10-may-2020"),
        ("15 June 2020", "https://www.gov.uk/government/news/rule-of-six-comes-into-effect-to-tackle-coronavirus"),
        ("04 July 2020", "https://www.gov.uk/government/news/prime-minister-announces-new-local-covid-alert-levels"),
        ("01 August 2020", "https://www.gov.uk/government/speeches/prime-ministers-statement-on-coronavirus-covid-19-19-december-2020"),
        ("03 August 2020", "https://www.gov.uk/government/speeches/pm-address-to-the-nation-on-coronavirus-23-march-2020"),
        ("31 August 2020", "https://www.gov.uk/government/speeches/pm-address-to-the-nation-on-coronavirus-23-march-2020"),
        ("14 September 2020", "https://www.gov.uk/government/news/prime-minister-confirms-move-to-step-4"),
        ("22 September 2020", "https://www.gov.uk/government/publications/step-3-covid-19-restrictions-posters-17-may-2021"),
        ("24 September 2020", "https://www.gov.uk/guidance/get-a-discount-with-the-eat-out-to-help-out-scheme"),
        ("14 October 2020", "https://www.london.gov.uk/press-releases/mayoral/sadiq-issues-statement-on-new-restrictions"),
        ("17 October 2020", "https://www.gov.uk/government/speeches/prime-ministers-statement-on-coronavirus-covid-19-31-july-2020"),
        ("05 November 2020", "https://www.gov.uk/government/news/prime-minister-confirms-move-to-plan-b-in-england"),
        ("02 December 2020", "https://www.gov.uk/government/publications/step-2-covid-19-restrictions-posters-12-april-2021"),
        ("16 December 2020", "https://www.gov.uk/government/publications/covid-19-winter-plan/covid-19-winter-plan"),
        ("20 December 2020", "https://www.gov.uk/government/speeches/pm-commons-statement-on-coronavirus-22-september-2020"),
        ("05 January 2021", "https://www.gov.uk/government/speeches/prime-ministers-statement-on-coronavirus-covid-19-16-december-2020"),
        ("08 March 2021", "https://www.gov.uk/government/news/pm-announces-easing-of-lockdown-restrictions-23-june-2020"),
        ("29 March 2021", "https://www.gov.uk/government/news/government-announces-further-measures-on-social-distancing"),
        ("12 April 2021", "https://www.gov.uk/government/news/prime-minister-announces-new-national-restrictions"),
        ("17 May 2021", "https://www.gov.uk/government/news/schools-and-colleges-to-reopen-from-tomorrow-as-part-of-step-one-of-the-roadmap"),
        ("19 July 2021", "https://www.gov.uk/government/news/england-to-return-to-plan-a-following-the-success-of-the-booster-programme"),
        ("13 December 2021", "https://www.gov.uk/government/speeches/business-secretarys-statement-on-coronavirus-covid-19-9-june-2020"),
        ("27 January 2022", "https://www.gov.uk/government/speeches/pm-statement-at-coronavirus-press-conference-29-march-2021")
    ]
)
def test_timeline(page: Page, date, res_url):
    try:
        # Navigate to timeline page
        page.goto("http://127.0.0.1:5000/timeline")

        # Wait for timeline container to be visible
        page.wait_for_selector(".timeline-container", timeout=10000)

        # Wait for timeline cards to be visible
        expect(page.locator(".timeline-card").first).to_be_visible(timeout=10000)

        cards = page.locator(".timeline-card")
        found = False

        # Print total number of cards for debugging
        total_cards = cards.count()

        for i in range(total_cards):
            card = cards.nth(i)

            # Wait for date element to be visible
            expect(card.locator(".timeline-date")).to_be_visible(timeout=5000)

            # Get and normalize the date
            card_date = card.locator(".timeline-date").inner_text().strip()
            normalized_card_date = card_date.lower().replace(",", "").strip()
            normalized_expected_date = date.lower().replace(",", "").strip()

            if normalized_card_date == normalized_expected_date:
                # Wait for source link to be visible and clickable
                link = card.locator(".timeline-source a")
                expect(link).to_be_visible(timeout=5000)

                # Verify link attributes
                href = link.get_attribute("href")
                target = link.get_attribute("target")
                rel = link.get_attribute("rel")

                assert href == res_url, f"Link URL mismatch. Expected: {res_url}, Got: {href}"
                assert target == "_blank", "Link should open in new tab"
                assert rel == "noopener noreferrer", "Link should have security attributes"

                # Verify link text
                link_text = link.inner_text()
                assert link_text == "Source →", "Link should have correct text"

                found = True
                print(f"Successfully verified link for date {date}")
                break

        if not found:
            raise AssertionError(f"No timeline card found with date '{date}' (normalized to '{normalized_expected_date}')")

    except Exception as e:
        print(f"Test failed with error: {str(e)}")
        # Take a screenshot on failure
        raise