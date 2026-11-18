---
Django ER Diagram
---
erDiagram
LogEntry {
    AutoField id
    DateTimeField action_time
    ForeignKey user
    ForeignKey content_type
    TextField object_id
    CharField object_repr
    PositiveSmallIntegerField action_flag
    TextField change_message
}
Permission {
    AutoField id
    CharField name
    ForeignKey content_type
    CharField codename
}
Group {
    AutoField id
    CharField name
    ManyToManyField permissions
}
User {
    AutoField id
    CharField password
    DateTimeField last_login
    BooleanField is_superuser
    CharField username
    CharField first_name
    CharField last_name
    CharField email
    BooleanField is_staff
    BooleanField is_active
    DateTimeField date_joined
    ManyToManyField groups
    ManyToManyField user_permissions
}
ContentType {
    AutoField id
    CharField app_label
    CharField model
}
Session {
    CharField session_key
    TextField session_data
    DateTimeField expire_date
}
Country {
    AutoField id
    CharField name
    CharField name_ascii
    SlugField slug
    IntegerField geoname_id
    TextField alternate_names
    CharField code2
    CharField code3
    CharField continent
    CharField tld
    CharField phone
}
Region {
    AutoField id
    CharField name
    CharField name_ascii
    SlugField slug
    IntegerField geoname_id
    TextField alternate_names
    CharField display_name
    CharField geoname_code
    ForeignKey country
}
SubRegion {
    AutoField id
    CharField name
    CharField name_ascii
    SlugField slug
    IntegerField geoname_id
    TextField alternate_names
    CharField display_name
    CharField geoname_code
    ForeignKey country
    ForeignKey region
}
City {
    AutoField id
    CharField name
    CharField name_ascii
    SlugField slug
    IntegerField geoname_id
    TextField alternate_names
    CharField display_name
    TextField search_names
    DecimalField latitude
    DecimalField longitude
    ForeignKey subregion
    ForeignKey region
    ForeignKey country
    BigIntegerField population
    CharField feature_code
    CharField timezone
}
Token {
    CharField key
    OneToOneField user
    DateTimeField created
}
TokenProxy {
    CharField key
    OneToOneField user
    DateTimeField created
}
Site {
    AutoField id
    CharField domain
    CharField name
}
EmailAddress {
    AutoField id
    ForeignKey user
    CharField email
    BooleanField verified
    BooleanField primary
}
EmailConfirmation {
    AutoField id
    ForeignKey email_address
    DateTimeField created
    DateTimeField sent
    CharField key
}
SocialApp {
    AutoField id
    CharField provider
    CharField provider_id
    CharField name
    CharField client_id
    CharField secret
    CharField key
    JSONField settings
    ManyToManyField sites
}
SocialAccount {
    AutoField id
    ForeignKey user
    CharField provider
    CharField uid
    DateTimeField last_login
    DateTimeField date_joined
    JSONField extra_data
}
SocialToken {
    AutoField id
    ForeignKey app
    ForeignKey account
    TextField token
    TextField token_secret
    DateTimeField expires_at
}
CompanyRegistrars {
    BigAutoField id
    CharField name
    CharField alias
    CharField sebi_reg_number
    ForeignKey city
    ForeignKey state
    CharField phone
    CharField fax
    CharField email
    CharField website
    CharField logo
    TextField address
    TextField about
    TextField html_content
    DateTimeField created_at
    DateTimeField updated_at
}
IndustryCategory {
    AutoField id
    CharField Name
    CharField Alias
}
IndustryCategoryAlias {
    BigAutoField id
    ForeignKey category
    CharField alias
}
SectorCategory {
    BigAutoField id
    CharField name
    DecimalField pe_ratio
    DecimalField total_earnings
    DecimalField earnings_growth_pct
    CharField trend
    CharField url_mc
    ManyToManyField industries
}
BusinessHouses {
    AutoField id
    CharField name
    CharField alias
    CharField logo
    CharField url_mw4m
    CharField url_dhan
    ManyToManyField companies
}
ShareDetails {
    AutoField id
    CharField isin
    CharField name
    CharField alias
    CharField series
    BooleanField is_listed
    BooleanField is_trade
    BooleanField is_derivative
    CharField country
    CharField currency
    DateField listing_date
    DecimalField face_value
    PositiveIntegerField market_lot
    PositiveIntegerField lot_size
    IntegerField bse_group
    DecimalField paidup_value
    DecimalField tick_size
    DecimalField impact_cost
    DecimalField margin_rate
    DecimalField change_1d
    DecimalField high_52w
    DecimalField low_52w
    ForeignKey industry_micro
    ForeignKey sector
    ForeignKey industry_type
    ForeignKey industry_basic
    IntegerField stock_score
    IntegerField stock_score_quality
    IntegerField stock_score_growth
    IntegerField stock_score_value
    IntegerField stock_score_tech
    DateTimeField score_updated_at
    DecimalField market_cap
    BigIntegerField enterprise_value
    BigIntegerField issued_shares
    BigIntegerField shares_float
    BigIntegerField shares_outstanding
    BigIntegerField imp_outst_shares
    IntegerField cap_paid
    DecimalField eps
    DecimalField eps_ttm
    DecimalField eps_diluted
    DecimalField eps_forw
    DecimalField price_eps_year
    DecimalField eps_year
    DecimalField roce
    DecimalField roe
    DecimalField roa
    DecimalField opm
    DecimalField total_cash
    DecimalField total_cash_share
    DecimalField ebitda
    DecimalField ebitda_enterprise
    DecimalField revenue_enterprise
    DecimalField ebitda_margins
    DecimalField gross_margins
    DecimalField earning_growth
    DecimalField qoq_growth
    DecimalField operating_cash_flow
    DecimalField free_cash_flow
    DecimalField gross_profit
    DecimalField revenue_growth
    DecimalField revenue_share
    DecimalField revenue_total
    DecimalField current_ratio
    DecimalField quick_ratio
    BigIntegerField net_income_common
    DecimalField pe_ratio
    DecimalField pe_ttm
    DecimalField trailing_peg_ratio
    DecimalField pe_forw
    DecimalField price_book
    DecimalField book_value
    DecimalField mcap_sales
    CharField trend
    DecimalField debt
    DecimalField debt_equity
    DecimalField debt_pct
    DecimalField vwap
    DecimalField dividend_yield
    DecimalField beta
    DecimalField beta_mth3
    DecimalField beta_mth6
    DecimalField beta_yr1
    DecimalField beta_yr3
    IntegerField durability
    IntegerField valuation
    IntegerField momentum
    CharField performance
    IntegerField piotroski_score
    IntegerField rank_smcp
    DecimalField holdings_institutions
    DecimalField holdings_insiders
    CharField id_mc
    PositiveIntegerField nse_inv
    PositiveIntegerField bse_inv
    PositiveIntegerField fut_inv
    CharField company_website
    CharField url_logo
    CharField url_bse
    CharField url_nse
    CharField url_mc
    CharField url_tl
    CharField url_sc
    CharField url_tsr
    CharField url_t4
    CharField url_bs
    CharField url_et
    CharField url_inv_nse
    CharField url_inv_bse
    CharField url_inv_fut
    CharField url_ipo_mc
    CharField url_ipo_cg
    CharField url_etm
    IntegerField report_id
    CharField repo_number
    IntegerField incorp_year
    CharField fin_comment
    TextField about
    TextField history
    SlugField slug
}
ShareAlias {
    BigAutoField id
    ForeignKey share
    CharField alias
}
CompanyDetails {
    BigAutoField id
    CharField isin
    CharField name
    SlugField slug
    BooleanField slug_locked
    CharField country
    CharField series
    ForeignKey sector
    CharField symbol
    CharField wkn_code
    CharField url_dd
}
NseBhav {
    BigAutoField id
    ForeignKey share
    FloatField open
    FloatField high
    FloatField low
    FloatField close
    FloatField last
    BigIntegerField qty
    FloatField value
    BigIntegerField trades
    BigIntegerField delivery
    DateField date
}
NseSmeBhav {
    BigAutoField id
    ForeignKey share
    FloatField open
    FloatField high
    FloatField low
    FloatField last
    FloatField close
    BigIntegerField qty
    FloatField value
    BigIntegerField trades
    BigIntegerField delivery
    DateField date
}
BseBhav {
    BigAutoField id
    ForeignKey share
    FloatField open
    FloatField high
    FloatField low
    FloatField close
    FloatField last
    BigIntegerField qty
    FloatField value
    BigIntegerField trades
    BigIntegerField delivery
    DateField date
}
ShareCode {
    AutoField id
    OneToOneField share
    CharField nse
    PositiveIntegerField bse
    CharField yahoo
}
InvestorDetails {
    BigAutoField id
    CharField name
}
EquityDeals {
    BigAutoField id
    ForeignKey share
    IntegerField market_type
    IntegerField deal_type
    IntegerField action
    FloatField price
    BigIntegerField qty
    DateField date
    ForeignKey invester
}
ClientCategories {
    BigAutoField id
    CharField Category
}
TradeTypes {
    BigAutoField id
    CharField Type
}
TradeRegulationTypes {
    AutoField id
    CharField type
}
SecurityTypes {
    AutoField id
    CharField Name
}
TransactionModes {
    AutoField id
    CharField Mode
}
InsiderTrading {
    AutoField id
    ForeignKey share
    ForeignKey investor
    ForeignKey client_category
    ForeignKey action
    DateField ex_date
    IntegerField qty
    IntegerField pth_qty
    FloatField pth_pcr
    FloatField pcr_trade
    FloatField avg_price
    DateField s_date
    DateField e_date
    ForeignKey regulation
    ForeignKey sec_type
    ForeignKey mode
}
FIIDIIEquity {
    DateField date
    DecimalField fii_gross_purchase
    DecimalField fii_gross_sales
    DecimalField dii_gross_purchase
    DecimalField dii_gross_sales
}
CompanyNameChange {
    CharField code
    CharField old_name
    CharField new_name
    DateField date
}
CompanyDelisted {
    BigAutoField id
    CharField code
    CharField name
    CharField type
    DateField date
}
ShareBonus {
    BigAutoField id
    ForeignKey share
    CharField ratio
    DateField date
    DateField ann_date
}
ShareDividend {
    BigAutoField id
    ForeignKey share
    DateField ann_date
    DateField ex_date
    DateField rec_date
    FloatField percent
    FloatField amount
    CharField type
    TextField remarks
}
ShareSplit {
    BigAutoField id
    ForeignKey share
    IntegerField old
    IntegerField new
    DateField date
    DateField ann_date
}
ShareRights {
    BigAutoField id
    ForeignKey share
    CharField ratio
    IntegerField face_value
    FloatField premium
    DateField record_date
    DateField ann_date
    DateField ex_date
}
BoardMeetings {
    BigAutoField id
    ForeignKey share
    DateField date
    CharField purpose
    TextField remarks
}
AGMEGM {
    BigAutoField id
    ForeignKey share
    DateField meeting_date
    DateField ann_date
    CharField purpose
    TextField remarks
}
CodeChange {
    ForeignKey share
    CharField new
    CharField old
    DateField date
}
DBUpdateStatus {
    BigAutoField id
    CharField type
    DateField date
}
ShareAnalysisReport {
    BigAutoField id
    ForeignKey share
    TextField quality
    TextField growth
    TextField value
    TextField tech
    TextField prons
    TextField cons
    DateField updated_at
}
ShareCapitalStructure {
    BigAutoField id
    ForeignKey share
    PositiveIntegerField period_from
    PositiveIntegerField period_to
    CharField instrument
    DecimalField auth_capital
    DecimalField issued_capital
    PositiveBigIntegerField share_qty
    DecimalField face_value
}
FinParticulars {
    BigAutoField id
    CharField name
    CharField alias
    TextField description
    IntegerField category
    ForeignKey parent
    CharField statement_type
    CharField unit
    PositiveIntegerField display_order
    BooleanField is_active
}
HoldingPatterns {
    BigAutoField id
    ForeignKey share
    ForeignKey particular
    PositiveIntegerField year
    PositiveSmallIntegerField quarter
    DecimalField value
}
HoldingsPatternSummary {
    BigAutoField id
    ForeignKey share
    CharField particular
    DecimalField value
    DateField date
}
FinData {
    BigAutoField id
    ForeignKey share
    IntegerField category
    IntegerField period_type
    ForeignKey data_type
    ForeignKey particular
    PositiveIntegerField year
    PositiveSmallIntegerField quarter
    DecimalField value
    CharField unit
    DateTimeField created_at
    DateTimeField updated_at
}
CompanyPerformanceMatrices {
    BigAutoField id
    ForeignKey share
    ForeignKey particular
    PositiveSmallIntegerField period
    DecimalField value
    DateTimeField created_at
    DateTimeField updated_at
}
CompanyProsCons {
    BigAutoField id
    ForeignKey share
    CharField data_type
    PositiveSmallIntegerField quarter
    TextField text
    DateTimeField created_at
    PositiveIntegerField year
}
StocksRecommendations {
    BigAutoField id
    ForeignKey share
    IntegerField reco_type
    DecimalField price
    DecimalField target
    ForeignKey broker
    DateField date
    DateField tgt_date
    CharField url_pdf
}
ShareQGVTScore {
    BigAutoField id
    ForeignKey share
    CharField ann_type
    DateTimeField date
    TextField positive
    TextField negative
    JSONField positive_json
    JSONField negative_json
    CharField keywords
    PositiveSmallIntegerField score
    DateTimeField created_at
    DateTimeField updated_at
}
CashFlow {
    BigAutoField id
    ForeignKey share
    PositiveSmallIntegerField period_type
    ForeignKey particular
    PositiveIntegerField year
    PositiveSmallIntegerField quarter
    DecimalField value
}
IncomeStatement {
    BigAutoField id
    ForeignKey share
    PositiveSmallIntegerField period_type
    ForeignKey particular
    PositiveIntegerField year
    PositiveSmallIntegerField quarter
    DecimalField value
}
BalanceSheet {
    BigAutoField id
    ForeignKey share
    PositiveSmallIntegerField period_type
    ForeignKey particular
    PositiveIntegerField year
    PositiveSmallIntegerField quarter
    DecimalField value
}
CompanyFinancials {
    BigAutoField id
    ForeignKey share
    PositiveSmallIntegerField period_type
    ForeignKey particular
    PositiveIntegerField year
    PositiveSmallIntegerField quarter
    DecimalField value
}
EarningDate {
    BigAutoField id
    ForeignKey share
    DateTimeField earnings_date
    DecimalField eps_estimate
    DecimalField reported_eps
    CharField event_type
}
EarningHistory {
    BigAutoField id
    ForeignKey share
    DateField quarter
    DecimalField eps_actual
    DecimalField eps_estimate
}
ShareAllocation {
    BigAutoField id
    ForeignKey share
    DecimalField percent
    CharField category
    ManyToManyField peers
}
StockNotes {
    BigAutoField id
    ForeignKey share
    ForeignKey user
    PositiveSmallIntegerField note_type
    CharField title
    TextField content
    JSONField tags
    PositiveSmallIntegerField importance
    CharField source_url
    DateField reference_date
    BooleanField is_private
    DateTimeField created_at
    DateTimeField updated_at
}
TrackedExperts {
    BigAutoField id
    ForeignKey expert
    DateTimeField added_on
    BooleanField is_active
    TextField notes
}
ResearchNotes {
    BigAutoField id
    TextField notes
    DateTimeField created_at
    ManyToManyField shares
}
FundsTrack {
    BigAutoField id
    ForeignKey fund
    ForeignKey client
    TextField notes
}
Client {
    BigAutoField id
    CharField name
    CharField aadhaar
    CharField pan
    CharField email
    JSONField token
    JSONField credentials
    TextField description
    FileField photo
}
ClientAddress {
    BigAutoField id
    ForeignKey client
    CharField address_type
    CharField street
    CharField city
    CharField state
    CharField postal_code
    CharField country
    BooleanField is_primary
    TextField notes
}
ClientContact {
    BigAutoField id
    ForeignKey client
    CharField first_name
    CharField last_name
    CharField email
    CharField phone
    CharField mobile
    CharField position
    BooleanField is_primary
    TextField notes
    DateTimeField created_at
    DateTimeField updated_at
}
ClientInteraction {
    BigAutoField id
    ForeignKey client
    ForeignKey contact
    CharField interaction_type
    CharField subject
    TextField notes
    DateTimeField date
    PositiveIntegerField duration
    BooleanField follow_up_required
    DateField follow_up_date
    TextField follow_up_notes
    ForeignKey created_by
    DateTimeField created_at
    DateTimeField updated_at
    ManyToManyField participants
}
ClientNote {
    BigAutoField id
    ForeignKey client
    CharField title
    TextField content
    PositiveSmallIntegerField priority
    ForeignKey created_by
    DateTimeField created_at
    DateTimeField updated_at
    BooleanField is_resolved
}
Transactions {
    BigAutoField id
    ForeignKey client
    ForeignKey share
    CharField type
    PositiveBigIntegerField qty
    DecimalField price
    BigIntegerField trade_id
    DateTimeField date
    CharField opt_type
    DecimalField strk_price
    DateField exp_date
    PositiveSmallIntegerField broker
}
ShareWatchlist {
    BigAutoField id
    ForeignKey client
    ForeignKey share
    TextField notes
}
ShortPosition {
    CharField id
    ForeignKey share
    DateField open_date
    PositiveIntegerField open_quantity
    DecimalField open_price
    BooleanField is_fully_closed
    CharField status
    TextField notes
    DateTimeField created_at
    DateTimeField updated_at
}
ShortPositionClose {
    BigAutoField id
    ForeignKey share
    DateField close_date
    PositiveIntegerField quantity
    DecimalField price
    TextField notes
    DateTimeField created_at
    DateTimeField updated_at
}
Hedge {
    BigAutoField id
    ForeignKey share
    DateField hedge_date
    PositiveIntegerField quantity
    DecimalField price
    DateField close_date
    DecimalField close_price
    BooleanField is_closed
    TextField notes
    DateTimeField created_at
    DateTimeField updated_at
}
WorldStockExchanges {
    BigAutoField id
    CharField code
    CharField name
    SlugField slug
    CharField country
    ForeignKey city
    CharField url
    CharField url_logo
    BooleanField is_active
    DateField established_date
    CharField timezone
    CharField currency
    DecimalField market_cap
}
WorldIndices {
    BigAutoField id
    CharField indice
    CharField country
    ForeignKey exchange
    IntegerField type
    IntegerField category
    CharField yahoo_id
    PositiveIntegerField inv_id
    CharField inv_url
    CharField url
    CharField nse_file_url
    CharField url_dhan
}
IndiceCompositions {
    BigAutoField id
    ForeignKey share
    ForeignKey indice
    FloatField weight
}
IndiceBhav {
    BigAutoField id
    ForeignKey indice
    DecimalField open
    DecimalField high
    DecimalField low
    DecimalField close
    PositiveIntegerField volume
    DecimalField turnover
    DecimalField pe
    DecimalField pb
    DecimalField div_yield
    DateField date
}
Segment {
    BigAutoField id
    CharField name
    CharField segment_type
    TextField description
    DecimalField market_cap
    BooleanField is_active
    IntegerField performance_rating
    FloatField volatility_index
    FloatField growth_potential
}
Commodity {
    BigAutoField id
    CharField name
    TextField description
    ForeignKey segment
    CharField ticker_symbol
    BooleanField is_tradable
}
BhavCopy {
    BigAutoField id
    ForeignKey commodity
    DecimalField open_price
    DecimalField high_price
    DecimalField low_price
    DecimalField close_price
    PositiveIntegerField volume
    DecimalField day_change
    DecimalField change_percent
    DecimalField vwap
    PositiveIntegerField delivery_volume
    DecimalField delivery_percent
    DateField date
}
NewsSource {
    BigAutoField id
    CharField name
    SlugField slug
    TextField description
}
NewsCategory {
    BigAutoField id
    CharField name
    SlugField slug
    TextField description
}
NewsTags {
    BigAutoField id
    CharField name
    SlugField slug
}
Persons {
    BigAutoField id
    CharField name
    SlugField slug
    TextField details
    JSONField social_media_links
}
ImageDetails {
    BigAutoField id
    CharField url
    CharField title
    CharField alt_text
}
NewsDetails {
    IntegerField id
    CharField title
    SlugField slug
    TextField sub_title
    ForeignKey img_url
    CharField img_text
    CharField url
    DateTimeField date
    ForeignKey source
    TextField details
    ManyToManyField category
    ManyToManyField authors
    ManyToManyField tags
}
MarketExperts {
    BigAutoField id
    CharField name
    CharField alias
    CharField title
    IntegerField category
    CharField url
    FileField photo
    CharField linkedIn
    CharField url_tl
    TextField details
    SlugField slug
    BooleanField is_active
}
AliasExperts {
    BigAutoField id
    CharField alias
    ForeignKey name
}
ExpertsHoldings {
    BigAutoField id
    ForeignKey share
    ForeignKey expert
    BigIntegerField qty
    FloatField percent
    IntegerField quarter
    IntegerField year
}
KeywordsRejection {
    BigAutoField id
    CharField keyword
}
Custodians {
    BigAutoField id
    CharField name
    CharField alias
    TextField details
    DateTimeField created_at
    DateTimeField updated_at
}
Auditors {
    BigAutoField id
    CharField name
    CharField alias
    CharField url
    TextField details
    DateTimeField created_at
    DateTimeField updated_at
}
Company {
    BigAutoField id
    CharField name
    CharField alias
    CharField url
    CharField registration_number
    DateField established_date
    TextField details
    DateTimeField created_at
    DateTimeField updated_at
}
AMCDetails {
    IntegerField amfi_id
    CharField name
    CharField short_name
    DateField setup_date
    DateField incorporation_date
    TextField address
    CharField telephone
    CharField fax
    CharField email
    CharField url_mc
    CharField url_etm
    CharField url_tl
    CharField logo_url
    CharField website
    DateTimeField created_at
    DateTimeField updated_at
    ManyToManyField sponsors
    ManyToManyField trustees_company
    ManyToManyField trustees_person
    ManyToManyField chairman
    ManyToManyField ceo
    ManyToManyField cio
    ManyToManyField compliance_officer
    ManyToManyField investor_service_officer
    ManyToManyField auditors
    ManyToManyField custodians
    ManyToManyField registrars
}
AMCAlias {
    BigAutoField id
    ForeignKey house
    CharField alias
}
OptionTypes {
    BigAutoField id
    CharField name
}
FundsCategory {
    BigAutoField id
    CharField name
    FloatField standard_deviation
    FloatField beta
    FloatField sharp_ratio
    FloatField treynor_ratio
    FloatField jensens_alpha
    TextField description
}
CategoryAUM {
    BigAutoField id
    ForeignKey category
    DateField date
    DecimalField value
}
FundsBenchmark {
    BigAutoField id
    CharField name
    CharField category
    TextField description
}
FundRiskRatios {
    BigAutoField id
    ForeignKey fund
    DateField report_date
    FloatField standard_deviation
    FloatField beta
    FloatField sharp_ratio
    FloatField treynor_ratio
    FloatField jensens_alpha
}
CategoryRiskRatios {
    BigAutoField id
    ForeignKey category
    DateField report_date
    FloatField standard_deviation
    FloatField beta
    FloatField sharp_ratio
    FloatField treynor_ratio
    FloatField jensens_alpha
}
FundsDetail {
    BigAutoField id
    PositiveIntegerField scheme_code
    PositiveIntegerField uid
    CharField name
    ForeignKey amc
    IntegerField fund_plan
    ForeignKey fund_option
    IntegerField fund_type
    ForeignKey fund_category
    ForeignKey benchmark
    IntegerField riskometer
    IntegerField crisil_rating
    DateField launch_date
    DateField close_date
    DecimalField expense_ratio
    CharField url_mc
    CharField url_etm
    CharField url_tl
    TextField load_structure
    TextField investment_objective
    TextField tax_implications
    DecimalField aum
    FloatField standard_deviation
    FloatField beta
    FloatField sharp_ratio
    FloatField treynor_ratio
    FloatField jensens_alpha
    FloatField portfolio_turnover_ratio
    ManyToManyField managers
}
HoldingsSummary {
    BigAutoField id
    ForeignKey fund
    DecimalField equity_holding
    DecimalField fo_holdings
    DecimalField foreign_equity_holding
    PositiveIntegerField no_of_stocks
    DecimalField portfolio_turnover_ratio
    DecimalField large_cap_investments
    DecimalField mid_cap_investments
    DecimalField small_cap_investments
    DecimalField others_investments
    DecimalField weight_stock_top_5_pct
    DecimalField weight_stock_top_10_pct
    DecimalField weight_sector_top_3_pct
    DateField as_of_date
}
EquityHoldings {
    BigAutoField id
    ForeignKey fund
    ForeignKey share
    PositiveIntegerField quantity
    FloatField value
    FloatField percentage
    DateField holding_date
}
FundsAUM {
    BigAutoField id
    ForeignKey fund
    DateField date
    DecimalField value
    DecimalField pct_category
}
InstrumentTypes {
    BigAutoField id
    CharField name
    CharField alias
}
HoldingsOthers {
    BigAutoField id
    ForeignKey fund
    ForeignKey instrument_type
    DecimalField weight_pct
    DateField date
}
CategorySummary {
    BigAutoField id
    ForeignKey category
    DateField report_date
    DecimalField avg_mcap
    IntegerField no_of_stocks
    DecimalField portfolio_turnover_ratio
    DecimalField weight_stock_top_5_pct
    DecimalField weight_stock_top_10_pct
    DecimalField weight_sector_top_3_pct
    DecimalField larg_cap_holdg_pct
    DecimalField mid_cap_holdg_pct
    DecimalField small_cap_holdg_pct
}
ShareHoldingHistory {
    BigAutoField id
    ForeignKey fund
    ForeignKey share
    DecimalField holding_pct
    DateField holding_date
}
Cryptocurrency {
    UUIDField id
    CharField symbol
    CharField name
    CharField coingecko_id
    IntegerField market_cap_rank
    BooleanField is_active
    DateTimeField created_at
    DateTimeField updated_at
}
BhavCopy {
    BigAutoField id
    ForeignKey crypto
    DateField date
    DecimalField open
    DecimalField high
    DecimalField low
    DecimalField close
    DecimalField adj_close
    BigIntegerField volume
}
LogEntry }|--|| User : user
LogEntry }|--|| ContentType : content_type
Permission }|--|| ContentType : content_type
Group }|--|{ Permission : permissions
User }|--|{ Group : groups
User }|--|{ Permission : user_permissions
Region }|--|| Country : country
SubRegion }|--|| Country : country
SubRegion }|--|| Region : region
City }|--|| SubRegion : subregion
City }|--|| Region : region
City }|--|| Country : country
Token ||--|| User : user
TokenProxy ||--|| User : user
EmailAddress }|--|| User : user
EmailConfirmation }|--|| EmailAddress : email_address
SocialApp }|--|{ Site : sites
SocialAccount }|--|| User : user
SocialToken }|--|| SocialApp : app
SocialToken }|--|| SocialAccount : account
CompanyRegistrars }|--|| City : city
CompanyRegistrars }|--|| Region : state
IndustryCategoryAlias }|--|| IndustryCategory : category
SectorCategory }|--|{ IndustryCategory : industries
BusinessHouses }|--|{ ShareDetails : companies
ShareDetails }|--|| IndustryCategory : industry_micro
ShareDetails }|--|| IndustryCategory : sector
ShareDetails }|--|| SectorCategory : industry_type
ShareDetails }|--|| IndustryCategory : industry_basic
ShareAlias }|--|| ShareDetails : share
CompanyDetails }|--|| IndustryCategory : sector
NseBhav }|--|| ShareDetails : share
NseSmeBhav }|--|| ShareDetails : share
BseBhav }|--|| ShareDetails : share
ShareCode ||--|| ShareDetails : share
EquityDeals }|--|| ShareDetails : share
EquityDeals }|--|| InvestorDetails : invester
InsiderTrading }|--|| ShareDetails : share
InsiderTrading }|--|| InvestorDetails : investor
InsiderTrading }|--|| ClientCategories : client_category
InsiderTrading }|--|| TradeTypes : action
InsiderTrading }|--|| TradeRegulationTypes : regulation
InsiderTrading }|--|| SecurityTypes : sec_type
InsiderTrading }|--|| TransactionModes : mode
ShareBonus }|--|| ShareDetails : share
ShareDividend }|--|| ShareDetails : share
ShareSplit }|--|| ShareDetails : share
ShareRights }|--|| ShareDetails : share
BoardMeetings }|--|| ShareDetails : share
AGMEGM }|--|| ShareDetails : share
CodeChange }|--|| ShareDetails : share
ShareAnalysisReport }|--|| ShareDetails : share
ShareCapitalStructure }|--|| ShareDetails : share
FinParticulars }|--|| FinParticulars : parent
HoldingPatterns }|--|| ShareDetails : share
HoldingPatterns }|--|| FinParticulars : particular
HoldingsPatternSummary }|--|| ShareDetails : share
FinData }|--|| ShareDetails : share
FinData }|--|| FinParticulars : data_type
FinData }|--|| FinParticulars : particular
CompanyPerformanceMatrices }|--|| ShareDetails : share
CompanyPerformanceMatrices }|--|| FinParticulars : particular
CompanyProsCons }|--|| ShareDetails : share
StocksRecommendations }|--|| ShareDetails : share
StocksRecommendations }|--|| MarketExperts : broker
ShareQGVTScore }|--|| ShareDetails : share
CashFlow }|--|| ShareDetails : share
CashFlow }|--|| FinParticulars : particular
IncomeStatement }|--|| ShareDetails : share
IncomeStatement }|--|| FinParticulars : particular
BalanceSheet }|--|| ShareDetails : share
BalanceSheet }|--|| FinParticulars : particular
CompanyFinancials }|--|| ShareDetails : share
CompanyFinancials }|--|| FinParticulars : particular
EarningDate }|--|| ShareDetails : share
EarningHistory }|--|| ShareDetails : share
ShareAllocation }|--|| ShareDetails : share
ShareAllocation }|--|{ ShareDetails : peers
StockNotes }|--|| ShareDetails : share
StockNotes }|--|| User : user
TrackedExperts }|--|| MarketExperts : expert
ResearchNotes }|--|{ ShareDetails : shares
FundsTrack }|--|| FundsDetail : fund
FundsTrack }|--|| Client : client
ClientAddress }|--|| Client : client
ClientContact }|--|| Client : client
ClientInteraction }|--|| Client : client
ClientInteraction }|--|| ClientContact : contact
ClientInteraction }|--|| User : created_by
ClientInteraction }|--|{ User : participants
ClientNote }|--|| Client : client
ClientNote }|--|| User : created_by
Transactions }|--|| Client : client
Transactions }|--|| ShareDetails : share
ShareWatchlist }|--|| Client : client
ShareWatchlist }|--|| ShareDetails : share
ShortPosition }|--|| ShareDetails : share
ShortPositionClose }|--|| ShortPosition : share
Hedge }|--|| ShortPosition : share
WorldStockExchanges }|--|| City : city
WorldIndices }|--|| WorldStockExchanges : exchange
IndiceCompositions }|--|| ShareDetails : share
IndiceCompositions }|--|| WorldIndices : indice
IndiceBhav }|--|| WorldIndices : indice
Commodity }|--|| Segment : segment
BhavCopy }|--|| Commodity : commodity
NewsDetails }|--|| ImageDetails : img_url
NewsDetails }|--|| NewsSource : source
NewsDetails }|--|{ NewsCategory : category
NewsDetails }|--|{ Persons : authors
NewsDetails }|--|{ NewsTags : tags
AliasExperts }|--|| MarketExperts : name
ExpertsHoldings }|--|| ShareDetails : share
ExpertsHoldings }|--|| MarketExperts : expert
AMCDetails }|--|{ Company : sponsors
AMCDetails }|--|{ Company : trustees_company
AMCDetails }|--|{ Persons : trustees_person
AMCDetails }|--|{ Persons : chairman
AMCDetails }|--|{ Persons : ceo
AMCDetails }|--|{ Persons : cio
AMCDetails }|--|{ Persons : compliance_officer
AMCDetails }|--|{ Persons : investor_service_officer
AMCDetails }|--|{ CompanyRegistrars : auditors
AMCDetails }|--|{ Company : custodians
AMCDetails }|--|{ CompanyRegistrars : registrars
AMCAlias }|--|| AMCDetails : house
CategoryAUM }|--|| FundsCategory : category
FundRiskRatios }|--|| FundsDetail : fund
CategoryRiskRatios }|--|| FundsCategory : category
FundsDetail }|--|| AMCDetails : amc
FundsDetail }|--|| OptionTypes : fund_option
FundsDetail }|--|| FundsCategory : fund_category
FundsDetail }|--|| FundsBenchmark : benchmark
FundsDetail }|--|{ Persons : managers
HoldingsSummary }|--|| FundsDetail : fund
EquityHoldings }|--|| FundsDetail : fund
EquityHoldings }|--|| ShareDetails : share
FundsAUM }|--|| FundsDetail : fund
HoldingsOthers }|--|| FundsDetail : fund
HoldingsOthers }|--|| InstrumentTypes : instrument_type
CategorySummary }|--|| FundsCategory : category
ShareHoldingHistory }|--|| FundsDetail : fund
ShareHoldingHistory }|--|| ShareDetails : share
BhavCopy }|--|| Cryptocurrency : crypto