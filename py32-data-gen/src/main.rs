use std::path::Path;

mod chips;
mod dma;
mod docs;
mod gpio_af;
mod header;
mod interrupts;
mod memory;
mod rcc;
mod registers;

#[macro_export]
macro_rules! regex {
    ($re:literal) => {{
        ::ref_thread_local::ref_thread_local! {
            static managed REGEX: ::regex::Regex = ::regex::Regex::new($re).unwrap();
        }
        <REGEX as ::ref_thread_local::RefThreadLocal<::regex::Regex>>::borrow(&REGEX)
    }};
}

struct Stopwatch {
    start: std::time::Instant,
    section_start: Option<std::time::Instant>,
}

impl Stopwatch {
    fn new() -> Self {
        eprintln!("Starting timer");
        let start = std::time::Instant::now();
        Self {
            start,
            section_start: None,
        }
    }

    fn section(&mut self, status: &str) {
        let now = std::time::Instant::now();
        self.print_done(now);
        eprintln!("  {status}");
        self.section_start = Some(now);
    }

    fn stop(self) {
        let now = std::time::Instant::now();
        self.print_done(now);
        let total_elapsed = now - self.start;
        eprintln!("Total time: {:.2} seconds", total_elapsed.as_secs_f32());
    }

    fn print_done(&self, now: std::time::Instant) {
        if let Some(section_start) = self.section_start {
            let elapsed = now - section_start;
            eprintln!("    done in {:.2} seconds", elapsed.as_secs_f32());
        }
    }
}

fn main() -> anyhow::Result<()> {
    pretty_env_logger::init();

    let mut stopwatch = Stopwatch::new();

    stopwatch.section("Parsing registers");
    let registers = registers::Registers::parse()?;
    registers.write()?;

    stopwatch.section("Parsing chips");

    let data_dir = Path::new("./data");

    let mut chip_meta_files: Vec<_> = std::fs::read_dir(data_dir.join("chips"))
        .unwrap()
        .filter_map(|res| res.unwrap().file_name().to_str().map(|s| s.to_string()))
        .filter(|s| s.ends_with(".yaml"))
        .filter(|s| s.starts_with("PY32"))
        .map(|s| s.strip_suffix(".yaml").unwrap().to_string())
        .collect();
    chip_meta_files.sort();

    println!("chips: {:?}", chip_meta_files);

    std::fs::create_dir_all("build/data/chips")?;

    //for name in &chip_meta_files {
    //    let meta_yaml_path = data_dir.join(&format!("chips/{}.yaml", name));
    //    let content = std::fs::read_to_string(&meta_yaml_path)?;
    //    let mut chip: py32_data_serde::Chip = serde_yaml::from_str(&content)?;
    //}

    /*
    stopwatch.section("Parsing headers");
    let headers = header::Headers::parse()?;

    stopwatch.section("Parsing other stuff");

    // stopwatch.section("Parsing registers");
    let registers = registers::Registers::parse()?;
    registers.write()?;

    // stopwatch.section("Parsing memories");
    let memories = memory::Memories::parse()?;

    // stopwatch.section("Parsing interrupts");
    let chip_interrupts = interrupts::ChipInterrupts::parse()?;

    // stopwatch.section("Parsing RCC registers");
    let peripheral_to_clock = rcc::ParsedRccs::parse(&registers)?;

    // stopwatch.section("Parsing docs");
    let docs = docs::Docs::parse()?;

    // stopwatch.section("Parsing DMA");
    let dma_channels = dma::DmaChannels::parse()?;

    // stopwatch.section("Parsing GPIO AF");
    let af = gpio_af::Af::parse()?;

    stopwatch.section("Parsing chip groups");
    let (chips, chip_groups) = chips::parse_groups()?;

    stopwatch.section("Processing chips");
    chips::dump_all_chips(
        chip_groups,
        headers,
        af,
        chip_interrupts,
        peripheral_to_clock,
        dma_channels,
        chips,
        memories,
        docs,
    )?;

    stopwatch.stop();
    */

    Ok(())
}