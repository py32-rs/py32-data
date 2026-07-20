use std::collections::{HashMap, HashSet};
use std::path::Path;

use py32_data_serde::{Chip, ChipConfig, Generic, Series};

mod registers;

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
    
    // Caching loaded files to avoid re-reading
    let mut generics: HashMap<String, Generic> = HashMap::new();
    let mut series_map: HashMap<String, Series> = HashMap::new();
    let mut die_peripherals: HashMap<String, Vec<py32_data_serde::chip::core::Peripheral>> = HashMap::new();
    let mut die_interrupts: HashMap<String, Vec<py32_data_serde::chip::core::Interrupt>> = HashMap::new();
    let mut die_dma_channels: HashMap<String, Vec<py32_data_serde::chip::core::DmaChannels>> = HashMap::new();
    let mut die_afs: HashMap<String, HashMap<String, Vec<py32_data_serde::chip::core::peripheral::Pin>>> = HashMap::new();
    let mut die_dma_requests: HashMap<String, HashMap<String, Vec<py32_data_serde::chip::core::peripheral::DmaChannel>>> = HashMap::new();
    let mut processed_generics = HashSet::new();

    for name in &chip_meta_files {
        let meta_yaml_path = data_dir.join(format!("chips/{}.yaml", name));
        let content = std::fs::read_to_string(&meta_yaml_path)?;
        let chip_cfg: ChipConfig = serde_yaml::from_str(&content)?;

        // Load generic
        let generic = if let Some(g) = generics.get(&chip_cfg.generic) {
            g.clone()
        } else {
            let gen_path = data_dir.join(format!("generics/{}.yaml", chip_cfg.generic));
            let gen_content = std::fs::read_to_string(&gen_path)?;
            let g: Generic = serde_yaml::from_str(&gen_content)?;
            generics.insert(chip_cfg.generic.clone(), g.clone());
            g
        };
        
        // Load series
        let series = if let Some(s) = series_map.get(&generic.series) {
            s.clone()
        } else {
            let s_path = data_dir.join(format!("series/{}.yaml", generic.series));
            let s_content = std::fs::read_to_string(&s_path)?;
            let s: Series = serde_yaml::from_str(&s_content)?;
            series_map.insert(generic.series.clone(), s.clone());
            s
        };
        
        let die_name = &series.die;
        
        // Load die components
        if !die_peripherals.contains_key(die_name) {
            let p_path = data_dir.join(format!("dies/{}/peripherals.yaml", die_name));
            if p_path.exists() {
                let p_content = std::fs::read_to_string(&p_path)?;
                let peris: Vec<py32_data_serde::chip::core::Peripheral> = serde_yaml::from_str(&p_content)?;
                die_peripherals.insert(die_name.clone(), peris);
            } else {
                die_peripherals.insert(die_name.clone(), vec![]);
            }
        }
        
        if !die_interrupts.contains_key(die_name) {
            let i_path = data_dir.join(format!("dies/{}/interrupts.yaml", die_name));
            if i_path.exists() {
                let i_content = std::fs::read_to_string(&i_path)?;
                let mut ints: Vec<py32_data_serde::chip::core::Interrupt> = serde_yaml::from_str(&i_content)?;
                ints.sort_by_key(|i| i.number);
                die_interrupts.insert(die_name.clone(), ints);
            } else {
                die_interrupts.insert(die_name.clone(), vec![]);
            }
        }
        
        if !die_dma_channels.contains_key(die_name) {
            let d_path = data_dir.join(format!("dies/{}/dma_channels.yaml", die_name));
            if d_path.exists() {
                let d_content = std::fs::read_to_string(&d_path)?;
                let dmas: Vec<py32_data_serde::chip::core::DmaChannels> = serde_yaml::from_str(&d_content)?;
                die_dma_channels.insert(die_name.clone(), dmas);
            } else {
                die_dma_channels.insert(die_name.clone(), vec![]);
            }
        }
        
        if !die_afs.contains_key(die_name) {
            let af_path = data_dir.join(format!("dies/{}/af.yaml", die_name));
            if af_path.exists() {
                let content = std::fs::read_to_string(&af_path)?;
                let afs: HashMap<String, Vec<py32_data_serde::chip::core::peripheral::Pin>> = serde_yaml::from_str(&content)?;
                die_afs.insert(die_name.clone(), afs);
            } else {
                die_afs.insert(die_name.clone(), HashMap::new());
            }
        }
        
        if !die_dma_requests.contains_key(die_name) {
            let req_path = data_dir.join(format!("dies/{}/dma_requests.yaml", die_name));
            let mut peripheral_dma_reqs = HashMap::new();
            if req_path.exists() {
                let content = std::fs::read_to_string(&req_path)?;
                let reqs: HashMap<String, u8> = serde_yaml::from_str(&content)?;
                
                let physical_channels = die_dma_channels.get(die_name).unwrap();
                
                for (signal, &remap) in &reqs {
                    let parts: Vec<&str> = signal.split('_').collect();
                    let (peripheral, sig) = if parts.len() == 1 {
                        (parts[0].to_string(), parts[0].to_string())
                    } else if parts.len() == 2 {
                        (parts[0].to_string(), parts[1].to_string())
                    } else {
                        panic!("Invalid DMA signal: {}", signal);
                    };
                    
                    if physical_channels.is_empty() {
                        let dma_channel = py32_data_serde::chip::core::peripheral::DmaChannel {
                            signal: sig.clone(),
                            dma: None,
                            channel: None,
                            request: Some(remap),
                        };
                        peripheral_dma_reqs
                            .entry(peripheral.clone())
                            .or_insert_with(Vec::new)
                            .push(dma_channel);
                    } else {
                        for phys in physical_channels {
                            let dma_channel = py32_data_serde::chip::core::peripheral::DmaChannel {
                                signal: sig.clone(),
                                dma: Some(phys.dma.clone()),
                                channel: Some(phys.name.clone()),
                                request: Some(remap),
                            };
                            peripheral_dma_reqs
                                .entry(peripheral.clone())
                                .or_insert_with(Vec::new)
                                .push(dma_channel);
                        }
                    }
                }
            }
            die_dma_requests.insert(die_name.clone(), peripheral_dma_reqs);
        }
        
        // Build the Core
        let mut final_peripherals = Vec::new();
        let current_afs = die_afs.get(die_name).unwrap();
        let current_dma_reqs = die_dma_requests.get(die_name).unwrap();
        
        for mut p in die_peripherals.get(die_name).unwrap().clone() {
            if !series.disabled_peripherals.contains(&p.name) {
                // inject afs
                if let Some(pins) = current_afs.get(&p.name) {
                    p.pins = pins.clone();
                }
                // inject dma requests
                if let Some(reqs) = current_dma_reqs.get(&p.name) {
                    p.dma_channels = reqs.clone();
                }
                
                // remove unused peripherals
                if let Some(registers) = &p.registers {
                    let path = Path::new(data_dir)
                        .join("registers")
                        .join(&format!("{}_{}.yaml", registers.kind, registers.version));
                    if path.exists() {
                        final_peripherals.push(p);
                    }
                } else {
                    final_peripherals.push(p);
                }
            }
        }
        
        let mut final_interrupts = Vec::new();
        for i in die_interrupts.get(die_name).unwrap() {
            if !series.disabled_interrupts.contains(&i.name) {
                final_interrupts.push(i.clone());
            }
        }
        
        let final_dma_channels = die_dma_channels.get(die_name).unwrap().clone();
        
        let core = py32_data_serde::chip::Core {
            name: "cm0p".to_string(), // Py32 uses Cortex-M0+
            peripherals: final_peripherals,
            nvic_priority_bits: Some(2), // typically 2
            interrupts: final_interrupts,
            dma_channels: final_dma_channels,
            include_interrupts: None,
            include_dma_channels: None,
            include_peripherals: None,
            include_afs: None,
        };

        let chip = Chip {
            name: chip_cfg.name,
            family: series.family.clone(),
            line: generic.series.clone(),
            device_id: chip_cfg.device_id,
            packages: chip_cfg.packages,
            memory: generic.memory.clone(),
            docs: chip_cfg.docs,
            cores: vec![core.clone()],
        };

        // generate chip json
        println!(
            "chip: {}, peripherals: {}",
            chip.name,
            chip.cores[0].peripherals.len()
        );
        let dump = serde_json::to_string_pretty(&chip)?;
        std::fs::write(format!("build/data/chips/{name}.json"), dump)?;
        
        if processed_generics.insert(chip_cfg.generic.clone()) {
            let generic_chip = Chip {
                name: chip_cfg.generic.clone(),
                family: series.family.clone(),
                line: generic.series.clone(),
                device_id: 0,
                packages: vec![],
                memory: generic.memory.clone(),
                docs: vec![],
                cores: vec![core.clone()],
            };
            let gen_dump = serde_json::to_string_pretty(&generic_chip)?;
            std::fs::write(format!("build/data/chips/{}.json", chip_cfg.generic), gen_dump)?;
        }
    }

    stopwatch.stop();

    Ok(())
}
