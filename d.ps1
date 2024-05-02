<# #>
param (
    [Parameter(Mandatory=$true)]
    [string]$CMD,

    [string]$peri
)

Switch ($CMD)
{
    "download-all" {
        echo TODO
    }
    "install-chiptool" {
        cargo install --git https://github.com/embassy-rs/chiptool
    }
    "extract-all" {
        rm -r -Force tmp/$peri -ErrorAction SilentlyContinue
        mkdir tmp/$peri | Out-Null

        $files = Get-ChildItem -Path "svd/PY32*"
        foreach ($f in $files) {
            $svd_path = $f
            $f = $f.Name.TrimStart("svd/PY32").TrimEnd("xx.svd")
            echo $f

            echo "processing $f ..."

            if (Test-Path -Path "transforms/$peri.yaml") {
                $trans_args = "--transform transforms/$peri.yaml"
            }

            $output = chiptool extract-peripheral $trans_args --svd $svd_path --peripheral $peri $args 2>&1
            if ($LASTEXITCODE -eq 0) {
                $output | Out-File -FilePath "tmp/$peri/$f.yaml"
                echo "OK"
            }
            else {
                if ($output -match 'peripheral not found') {
                    echo "No Peripheral"
                }
                else {
                    echo $output
                    echo "OTHER FAILURE"
                }
                Remove-Item -Path "tmp/$peri/$f.yaml" -ErrorAction SilentlyContinue
            }
        }
    }
    "gen" {
        Remove-Item -Recurse -Force "build/data" -ErrorAction SilentlyContinue
        cargo run -p py32-data-gen
        cargo run -p py32-metapac-gen
    }
    "ci" {
        echo "TODO $CMD"
    }
    default {
        echo "unknown command"
    }
}